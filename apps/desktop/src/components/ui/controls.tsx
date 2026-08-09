import type { ReactNode } from "react";

export function SettingRow({
  name,
  hint,
  children,
}: {
  name: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="settings-row">
      <span className="settings-row__label">
        <span className="settings-row__name">{name}</span>
        {hint && <span className="settings-row__hint">{hint}</span>}
      </span>
      {children}
    </div>
  );
}

export function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  label: string;
}) {
  return (
    <label className="switch">
      <span className="visually-hidden">{label}</span>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="switch__track" aria-hidden />
    </label>
  );
}

export function Segmented<T extends string>({
  value,
  options,
  onChange,
  label,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (next: T) => void;
  label: string;
}) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={value === option.value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function Slider({
  value,
  min,
  max,
  step,
  onChange,
  label,
  format,
}: {
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (next: number) => void;
  label: string;
  format?: (v: number) => string;
}) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--sp-2)" }}>
      <input
        type="range"
        aria-label={label}
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
      />
      <span className="settings-row__hint" style={{ minWidth: "4ch" }}>
        {format ? format(value) : value}
      </span>
    </span>
  );
}
