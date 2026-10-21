import React, { useState } from 'react';
import {
  ArrowDown,
  Binary,
  BrainCircuit,
  ChevronDown,
  CircleDot,
  Combine,
  Fingerprint,
  LockKeyhole,
  Sigma,
  SlidersHorizontal,
  Workflow,
  type LucideIcon,
} from 'lucide-react';


type StageId =
  | 'events'
  | 'preprocessing'
  | 'bilstm'
  | 'behavioral-embedding'
  | 'browser-static'
  | 'static-projection'
  | 'fusion'
  | 'fusion-mlp'
  | 'prediction';

interface PipelineStage {
  id: StageId;
  title: string;
  dimension: string;
  receives: string;
  calculates: string;
  rationale: string;
  sends: string;
  accent: 'cyan' | 'violet' | 'blue';
  icon: LucideIcon;
}

const STAGES: PipelineStage[] = [
  {
    id: 'events',
    title: 'Keystroke Events',
    dimension: 'Ordered variable-length sequence',
    receives: 'Generic event order, dwell, flight, press latency, pause status, and backspace status. No key identity is included.',
    calculates: 'Preserves the order and measured timing of each privacy-safe event.',
    rationale: 'Typing behavior is sequential, so averages alone cannot retain event-to-event relationships.',
    sends: 'An ordered event sequence to preprocessing.',
    accent: 'cyan',
    icon: Fingerprint,
  },
  {
    id: 'preprocessing',
    title: 'Six-Channel Preprocessing',
    dimension: 'Sequence × 6 channels',
    receives: 'Five stored event fields plus event order.',
    calculates: 'Derives normalized_position and applies saved training means and standard deviations to dwell_time, flight_time, press_to_press_latency, normalized_position, is_pause, and is_backspace.',
    rationale: 'Consistent channel order and training-time normalization make browser sessions compatible with the saved checkpoint.',
    sends: 'A normalized six-channel tensor and its true sequence length.',
    accent: 'cyan',
    icon: SlidersHorizontal,
  },
  {
    id: 'bilstm',
    title: 'Bidirectional LSTM',
    dimension: '32 hidden units × 2 directions',
    receives: 'The normalized variable-length six-channel sequence.',
    calculates: 'Reads timing relationships in forward and backward directions, with padding excluded from the packed sequence state.',
    rationale: 'A BiLSTM captures sequential timing relationships in both forward and backward directions.',
    sends: 'The final forward and backward states concatenated together.',
    accent: 'cyan',
    icon: BrainCircuit,
  },
  {
    id: 'behavioral-embedding',
    title: 'Behavioral Embedding',
    dimension: '64-D',
    receives: 'Two 32-unit BiLSTM direction states.',
    calculates: 'Concatenates the forward and backward states into one learned behavioral representation.',
    rationale: 'A compact embedding lets the fusion head use sequence information without flattening every event.',
    sends: '64 learned behavioral values to fusion.',
    accent: 'cyan',
    icon: Binary,
  },
  {
    id: 'browser-static',
    title: 'Browser-Local Static Analysis',
    dimension: '11 safe static features',
    receives: 'The transient password only inside the browser.',
    calculates: 'Derives password length, character-class counts, repetition information, and entropy-related features. The model excludes zxcvbn score and target-derived values from these 11 inputs.',
    rationale: 'Static characteristics are computed before transmission so plaintext never reaches the backend.',
    sends: 'Eleven numeric static features; never plaintext or key identities.',
    accent: 'violet',
    icon: LockKeyhole,
  },
  {
    id: 'static-projection',
    title: 'Static Projection',
    dimension: '11-D → 16-D',
    receives: 'Eleven normalized safe static password features.',
    calculates: 'Applies a learned linear projection followed by ReLU.',
    rationale: 'Transforms the eleven static password features into a compact learned representation.',
    sends: 'A 16-D static embedding to fusion.',
    accent: 'violet',
    icon: Sigma,
  },
  {
    id: 'fusion',
    title: 'Concatenation',
    dimension: '64-D + 16-D = 80-D',
    receives: 'The behavioral and static embeddings.',
    calculates: 'Concatenates both representations without claiming either branch is independently causal.',
    rationale: 'Combines static and behavioral representations before regression.',
    sends: 'An 80-D fused representation.',
    accent: 'blue',
    icon: Combine,
  },
  {
    id: 'fusion-mlp',
    title: 'Fusion MLP',
    dimension: '80-D → 32-unit ReLU → 1',
    receives: 'The 80-D concatenated representation.',
    calculates: 'Applies a 32-unit learned linear layer, ReLU, and a final scalar regression layer.',
    rationale: 'A small MLP learns nonlinear combinations of the two representations while remaining lightweight.',
    sends: 'One normalized regression output.',
    accent: 'blue',
    icon: Workflow,
  },
  {
    id: 'prediction',
    title: 'Experimental Prediction',
    dimension: 'log10 estimated guesses',
    receives: 'The normalized scalar model output and saved target scaling.',
    calculates: 'Converts the output back to the experimental log10 guessability scale.',
    rationale: 'Log10 compresses very large guess-count ranges into a more manageable prediction scale.',
    sends: 'An experimental behavior-augmented estimate for display and research persistence.',
    accent: 'blue',
    icon: CircleDot,
  },
];

const STAGE_BY_ID = new Map(STAGES.map((stage) => [stage.id, stage]));
const BEHAVIORAL_IDS: StageId[] = ['events', 'preprocessing', 'bilstm', 'behavioral-embedding'];
const STATIC_IDS: StageId[] = ['browser-static', 'static-projection'];
const FUSION_IDS: StageId[] = ['fusion', 'fusion-mlp', 'prediction'];

const accentClasses = {
  cyan: 'border-cyan-500/30 bg-cyan-500/5 text-cyan-200 hover:border-cyan-400/60 focus-visible:ring-cyan-400',
  violet: 'border-violet-500/30 bg-violet-500/5 text-violet-200 hover:border-violet-400/60 focus-visible:ring-violet-400',
  blue: 'border-blue-500/30 bg-blue-500/5 text-blue-200 hover:border-blue-400/60 focus-visible:ring-blue-400',
};

interface StageButtonProps {
  id: StageId;
  selected: boolean;
  onSelect: (id: StageId) => void;
}

const StageButton: React.FC<StageButtonProps> = ({ id, selected, onSelect }) => {
  const stage = STAGE_BY_ID.get(id)!;
  const Icon = stage.icon;
  return (
    <button
      type="button"
      data-stage={id}
      aria-pressed={selected}
      onClick={() => onSelect(id)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onSelect(id);
        }
      }}
      className={`w-full rounded-xl border p-3 text-left transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950 ${accentClasses[stage.accent]} ${selected ? 'ring-1 ring-current' : ''}`}
    >
      <span className="flex items-start gap-3">
        <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden={true} />
        <span>
          <span className="block text-xs font-semibold text-slate-100">{stage.title}</span>
          <span className="mt-1 block font-mono text-[11px]">{stage.dimension}</span>
        </span>
      </span>
    </button>
  );
};

const FlowArrow = () => (
  <div className="flex justify-center py-1 text-slate-600" aria-hidden="true">
    <ArrowDown className="h-4 w-4" />
  </div>
);

export const MLPipelineVisualization: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedId, setSelectedId] = useState<StageId>('bilstm');
  const selected = STAGE_BY_ID.get(selectedId)!;
  const SelectedIcon = selected.icon;

  const renderBranch = (ids: StageId[]) => ids.map((id, index) => (
    <React.Fragment key={id}>
      <StageButton id={id} selected={selectedId === id} onSelect={setSelectedId} />
      {index < ids.length - 1 ? <FlowArrow /> : null}
    </React.Fragment>
  ));

  return (
    <section className="mt-6 overflow-hidden rounded-xl border border-slate-800 bg-slate-950/70" aria-labelledby="ml-pipeline-heading">
      <button
        type="button"
        aria-expanded={isExpanded}
        aria-controls="ml-pipeline-content"
        onClick={() => setIsExpanded((current) => !current)}
        className="flex w-full items-center justify-between gap-4 p-4 text-left transition-colors hover:bg-slate-900/70 motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-400"
      >
        <span className="flex items-start gap-3">
          <BrainCircuit className="mt-0.5 h-5 w-5 shrink-0 text-blue-400" aria-hidden="true" />
          <span>
            <span id="ml-pipeline-heading" className="block text-sm font-semibold text-white">How the ML Model Works</span>
            <span className="mt-1 block text-xs text-slate-400">Explore the conceptual BiLSTM and static-feature fusion architecture.</span>
          </span>
        </span>
        <ChevronDown className={`h-5 w-5 shrink-0 text-slate-400 transition-transform motion-reduce:transition-none ${isExpanded ? 'rotate-180' : ''}`} aria-hidden="true" />
      </button>

      {isExpanded ? (
        <div id="ml-pipeline-content" className="border-t border-slate-800 p-4 sm:p-5">
          <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3 text-xs text-slate-300">
            This is a conceptual architecture visualization—not a display of live neural activations.
          </div>

          <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
            <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/[0.03] p-3 sm:p-4">
              <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-300">Behavioral branch</div>
              {renderBranch(BEHAVIORAL_IDS)}
            </div>
            <div className="rounded-xl border border-violet-500/20 bg-violet-500/[0.03] p-3 sm:p-4">
              <div className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-300">Static branch</div>
              {renderBranch(STATIC_IDS)}
              <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/70 p-3 text-[11px] leading-relaxed text-slate-400">
                Examples: password length, character-class counts, repetition information, and entropy-related features.
              </div>
            </div>
          </div>

          <div className="my-2 flex items-center justify-center gap-4 text-[11px] text-slate-500" aria-hidden="true">
            <span className="h-px flex-1 bg-gradient-to-r from-transparent to-cyan-500/40" />
            <span>64-D + 16-D</span>
            <span className="h-px flex-1 bg-gradient-to-l from-transparent to-violet-500/40" />
          </div>

          <div className="mx-auto max-w-2xl rounded-xl border border-blue-500/20 bg-blue-500/[0.03] p-3 sm:p-4">
            <div className="mb-3 text-center text-[11px] font-semibold uppercase tracking-[0.18em] text-blue-300">Fusion and regression</div>
            {renderBranch(FUSION_IDS)}
          </div>

          <div className="mt-5 rounded-xl border border-slate-800 bg-slate-900/70 p-4" aria-live="polite">
            <div className="flex items-center gap-2">
              <SelectedIcon className="h-4 w-4 text-blue-300" aria-hidden={true} />
              <h4 className="text-sm font-semibold text-white">{selected.title}</h4>
              <span className="ml-auto font-mono text-[10px] text-blue-300">{selected.dimension}</span>
            </div>
            <dl className="mt-3 grid grid-cols-1 gap-3 text-xs sm:grid-cols-2">
              <div><dt className="font-semibold text-slate-400">Receives</dt><dd className="mt-1 leading-relaxed text-slate-200">{selected.receives}</dd></div>
              <div><dt className="font-semibold text-slate-400">Calculates</dt><dd className="mt-1 leading-relaxed text-slate-200">{selected.calculates}</dd></div>
              <div><dt className="font-semibold text-slate-400">Why this technique</dt><dd className="mt-1 leading-relaxed text-slate-200">{selected.rationale}</dd></div>
              <div><dt className="font-semibold text-slate-400">Sends next</dt><dd className="mt-1 leading-relaxed text-slate-200">{selected.sends}</dd></div>
            </dl>
          </div>

          <div className="mt-5 grid grid-cols-1 gap-3 text-xs md:grid-cols-2">
            <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 text-emerald-100">
              <strong>Privacy:</strong> Plaintext remains browser-local. The backend receives only derived static features and privacy-safe numeric timing events.
            </div>
            <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-amber-100">
              <strong>Scientific limitation:</strong> The current checkpoint is synthetic-trained, the behavioral estimate is experimental, and real-user validation is still required. It is not a proven password-cracking probability or evidence that typing speed changes password strength.
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
};
