import React, { act, useState } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { PasswordTaskCard } from './PasswordTaskCard';


describe('PasswordTaskCard intentional focus changes', () => {
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

  function renderHarness() {
    const onSubmit = vi.fn();
    const onReset = vi.fn();

    function Harness() {
      const [invalidReason, setInvalidReason] = useState<string | null>(null);
      const intentionalInteraction = React.useRef(false);

      return (
        <>
          <PasswordTaskCard
            condition="untimed"
            hasConsented={true}
            passwordValue="Synthetic1!"
            isValid={invalidReason === null}
            invalidReason={invalidReason}
            recordsCount={11}
            attemptNumber={1}
            handleKeyDown={() => undefined}
            handleKeyUp={() => undefined}
            handlePaste={() => undefined}
            handleBlur={(event) => {
              const relatedTarget = event.relatedTarget;
              const movedToControl = relatedTarget instanceof HTMLElement
                && relatedTarget.dataset.experimentControl === 'true';
              if (intentionalInteraction.current || movedToControl) {
                intentionalInteraction.current = false;
                return;
              }
              setInvalidReason('Input focus lost during password entry');
            }}
            markIntentionalControlInteraction={() => {
              intentionalInteraction.current = true;
            }}
            handleChange={() => undefined}
            onReset={onReset}
            onSubmit={onSubmit}
            isSubmitting={false}
          />
          <output data-testid="validity">{invalidReason ?? 'valid'}</output>
        </>
      );
    }

    act(() => root.render(<Harness />));
    const input = container.querySelector('input[type="password"]') as HTMLInputElement;
    const buttons = Array.from(container.querySelectorAll('button'));
    const reset = buttons.find((button) => button.textContent?.includes('Reset Field'))!;
    const submit = buttons.find((button) => button.textContent?.includes('Submit Session'))!;
    const validity = container.querySelector('[data-testid="validity"]')!;
    return { input, reset, submit, validity, onReset, onSubmit };
  }

  function beginPointerInteraction(button: HTMLButtonElement) {
    button.dispatchEvent(new Event('pointerdown', { bubbles: true }));
  }

  function blurTo(input: HTMLInputElement, relatedTarget: EventTarget | null) {
    input.dispatchEvent(new FocusEvent('focusout', { bubbles: true, relatedTarget }));
  }

  it.each(['submit', 'reset'] as const)(
    'does not flag when %s pointer interaction starts before blur',
    (controlName) => {
      const harness = renderHarness();
      const control = harness[controlName];

      act(() => {
        beginPointerInteraction(control);
        blurTo(harness.input, control);
        control.click();
      });

      expect(harness.validity.textContent).toBe('valid');
      expect(controlName === 'submit' ? harness.onSubmit : harness.onReset).toHaveBeenCalledOnce();
    },
  );

  it('still flags an unrelated blur', () => {
    const harness = renderHarness();
    const unrelatedTarget = document.createElement('button');
    document.body.appendChild(unrelatedTarget);

    act(() => blurTo(harness.input, unrelatedTarget));

    expect(harness.validity.textContent).toBe('Input focus lost during password entry');
    unrelatedTarget.remove();
  });
});
