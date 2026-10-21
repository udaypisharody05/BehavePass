import React, { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { KeystrokeFeatureItem } from '../types';
import { KeystrokeTimeline } from './KeystrokeTimeline';


const sequence: KeystrokeFeatureItem[] = [
  {
    sequence_index: 0,
    dwell_time: 80,
    flight_time: null,
    press_to_press_latency: null,
    is_pause: false,
    is_backspace: false,
  },
  {
    sequence_index: 1,
    dwell_time: 120,
    flight_time: -40,
    press_to_press_latency: 40,
    is_pause: false,
    is_backspace: true,
  },
  {
    sequence_index: 2,
    dwell_time: 90,
    flight_time: 510,
    press_to_press_latency: 630,
    is_pause: true,
    is_backspace: false,
  },
];

describe('KeystrokeTimeline', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean })
      .IS_REACT_ACT_ENVIRONMENT = true;
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  function render(events: KeystrokeFeatureItem[] | null = sequence) {
    act(() => root.render(<KeystrokeTimeline sequence={events} />));
  }

  it('plots ordered real sequence values and omits null first-event points', () => {
    render();

    expect(container.querySelectorAll('[data-event-index]')).toHaveLength(3);
    expect(container.querySelector('[data-series="dwell_time"]')).not.toBeNull();
    expect(container.querySelector('[data-series="flight_time"]')).not.toBeNull();
    expect(container.querySelector('[data-series="press_to_press_latency"]')).not.toBeNull();
    expect(container.querySelectorAll('[data-point-series="flight_time"]')).toHaveLength(2);
    expect(container.querySelectorAll('[data-point-series="press_to_press_latency"]')).toHaveLength(2);
  });

  it('preserves negative flight values and exposes exact null values on focus', () => {
    render();

    expect(container.querySelector('[data-point-series="flight_time"][data-value="-40"]')).not.toBeNull();
    const firstEvent = container.querySelector('[data-event-index="0"]') as SVGGElement;
    act(() => firstEvent.dispatchEvent(new FocusEvent('focusin', { bubbles: true })));
    expect(container.textContent).toContain('Flight: Not available');
    expect(container.textContent).toContain('Latency: Not available');
  });

  it('renders pause and backspace indicators and exposes them accessibly', () => {
    render();

    expect(container.querySelectorAll('[data-indicator="pause"]')).toHaveLength(1);
    expect(container.querySelectorAll('[data-indicator="backspace"]')).toHaveLength(1);
    expect(container.querySelector('[data-event-index="1"]')?.getAttribute('aria-label')).toContain('backspace');
    expect(container.querySelector('[data-event-index="2"]')?.getAttribute('aria-label')).toContain('pause');
  });

  it('toggles individual timing series without altering the sequence', () => {
    render();
    const flightToggle = Array.from(container.querySelectorAll('input[type="checkbox"]'))
      .find((input) => input.parentElement?.textContent?.includes('Flight')) as HTMLInputElement;

    act(() => flightToggle.click());

    expect(container.querySelector('[data-series="flight_time"]')).toBeNull();
    expect(container.querySelectorAll('[data-event-index]')).toHaveLength(3);
    expect(container.querySelector('[data-series="dwell_time"]')).not.toBeNull();
  });

  it.each([[], null] as const)('shows an empty-sequence fallback for %s', (events) => {
    render(events as KeystrokeFeatureItem[] | null);

    expect(container.textContent).toContain('No privacy-safe event sequence is available');
    expect(container.querySelector('svg[role="img"]')).toBeNull();
  });
});
