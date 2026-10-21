import React, { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { MLPipelineVisualization } from './MLPipelineVisualization';


describe('MLPipelineVisualization', () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean })
      .IS_REACT_ACT_ENVIRONMENT = true;
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => root.render(<MLPipelineVisualization />));
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  function toggle() {
    const button = container.querySelector('[aria-controls="ml-pipeline-content"]') as HTMLButtonElement;
    act(() => button.click());
    return button;
  }

  it('expands and collapses the pipeline explainer', () => {
    const button = container.querySelector('[aria-controls="ml-pipeline-content"]') as HTMLButtonElement;
    expect(button.getAttribute('aria-expanded')).toBe('false');
    expect(container.querySelector('#ml-pipeline-content')).toBeNull();

    toggle();
    expect(button.getAttribute('aria-expanded')).toBe('true');
    expect(container.querySelector('#ml-pipeline-content')).not.toBeNull();

    toggle();
    expect(button.getAttribute('aria-expanded')).toBe('false');
    expect(container.querySelector('#ml-pipeline-content')).toBeNull();
  });

  it('renders the verified stages and dimensions', () => {
    toggle();

    expect(container.querySelectorAll('[data-stage]')).toHaveLength(9);
    expect(container.textContent).toContain('Sequence × 6 channels');
    expect(container.textContent).toContain('32 hidden units × 2 directions');
    expect(container.textContent).toContain('64-D');
    expect(container.textContent).toContain('11-D → 16-D');
    expect(container.textContent).toContain('64-D + 16-D = 80-D');
    expect(container.textContent).toContain('80-D → 32-unit ReLU → 1');

    const preprocessing = container.querySelector('[data-stage="preprocessing"]') as HTMLButtonElement;
    act(() => preprocessing.click());
    expect(container.textContent).toContain('normalized_position');
  });

  it('shows the selected stage explanation when clicked', () => {
    toggle();
    const fusion = container.querySelector('[data-stage="fusion"]') as HTMLButtonElement;

    act(() => fusion.click());

    expect(fusion.getAttribute('aria-pressed')).toBe('true');
    expect(container.textContent).toContain('Combines static and behavioral representations before regression.');
    expect(container.textContent).toContain('An 80-D fused representation.');
  });

  it('supports keyboard stage selection', () => {
    toggle();
    const staticProjection = container.querySelector('[data-stage="static-projection"]') as HTMLButtonElement;
    staticProjection.focus();

    act(() => staticProjection.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true })));

    expect(document.activeElement).toBe(staticProjection);
    expect(staticProjection.getAttribute('aria-pressed')).toBe('true');
    expect(container.textContent).toContain('Transforms the eleven static password features into a compact learned representation.');
  });

  it('shows privacy, provenance, and experimental limitations', () => {
    toggle();

    expect(container.textContent).toContain('Plaintext remains browser-local');
    expect(container.textContent).toContain('synthetic-trained');
    expect(container.textContent).toContain('behavioral estimate is experimental');
    expect(container.textContent).toContain('real-user validation is still required');
    expect(container.textContent).toContain('not a display of live neural activations');
  });
});
