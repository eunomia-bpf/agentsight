import { formatTime } from "../selectors";
import type { ViewState } from "../types";

interface Props {
  state: ViewState;
  min: number;
  max: number;
  onChange: (patch: Partial<ViewState>) => void;
}

const speeds = [1, 6, 24, 168];

export default function Playback({ state, min, max, onChange }: Props) {
  return (
    <section className="playback" aria-label="shared playback controls">
      <button
        className={`playback__button ${state.playing ? "is-playing" : ""}`}
        onClick={() => onChange({ playing: !state.playing })}
        aria-label={state.playing ? "Pause playback" : "Play history"}
      >
        {state.playing ? "Ⅱ" : "▶"}
      </button>
      <div className="playback__timeline">
        <div className="playback__labels">
          <span>{formatTime(min)}</span>
          <strong>{formatTime(state.cursorMs)} UTC</strong>
          <span>{formatTime(max)}</span>
        </div>
        <input
          data-testid="playback-slider"
          type="range"
          min={min}
          max={max}
          step={60_000}
          value={state.cursorMs}
          onChange={(event) =>
            onChange({ cursorMs: Number(event.currentTarget.value), playing: false })
          }
        />
      </div>
      <div className="speed-control" aria-label="playback speed">
        {speeds.map((speed) => (
          <button
            key={speed}
            className={state.speedHoursPerSecond === speed ? "is-active" : ""}
            onClick={() => onChange({ speedHoursPerSecond: speed })}
          >
            {speed < 24 ? `${speed}h/s` : `${speed / 24}d/s`}
          </button>
        ))}
      </div>
    </section>
  );
}
