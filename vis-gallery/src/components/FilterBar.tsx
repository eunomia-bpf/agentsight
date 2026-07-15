import type { ViewState } from "../types";

interface Props {
  state: ViewState;
  onChange: (patch: Partial<ViewState>) => void;
}

const vendors = ["claude", "codex", "gemini"];
const states = ["no_candidate", "unique_candidate", "ambiguous_candidates"];

function toggled(set: Set<string>, value: string): Set<string> {
  const next = new Set(set);
  if (next.has(value)) next.delete(value);
  else next.add(value);
  return next;
}

export default function FilterBar({ state, onChange }: Props) {
  return (
    <div className="filter-bar">
      <span className="filter-bar__label">Vendors</span>
      {vendors.map((vendor) => (
        <button
          key={vendor}
          className={`filter-chip vendor-${vendor} ${state.vendors.has(vendor) ? "is-active" : ""}`}
          onClick={() => onChange({ vendors: toggled(state.vendors, vendor) })}
        >
          {vendor}
        </button>
      ))}
      <span className="filter-bar__divider" />
      <span className="filter-bar__label">Join state</span>
      {states.map((value) => (
        <button
          key={value}
          className={`filter-chip ${state.associationStates.has(value) ? "is-active" : ""}`}
          onClick={() =>
            onChange({ associationStates: toggled(state.associationStates, value) })
          }
        >
          {value.replaceAll("_", " ")}
        </button>
      ))}
      {(state.selectedPath || state.selectedSession) && (
        <button
          className="filter-chip filter-chip--clear"
          onClick={() => onChange({ selectedPath: null, selectedSession: null })}
        >
          clear focus ×
        </button>
      )}
    </div>
  );
}
