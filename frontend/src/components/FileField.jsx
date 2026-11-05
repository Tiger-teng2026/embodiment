import { useRef } from "react";

export default function FileField({ label, hint, accept, fileName, action, onFile }) {
  const inputRef = useRef(null);
  return (
    <div>
      <p className="label">{label}</p>
      <p className="hint mb-3">{hint}</p>
      <button type="button" className="btn-ghost" onClick={() => inputRef.current?.click()}>
        {action}
      </button>
      {fileName ? <p className="mt-2 truncate text-sm text-zinc-800">{fileName}</p> : null}
      <input
        ref={inputRef}
        className="sr-only"
        type="file"
        accept={accept}
        onChange={(event) => {
          onFile(event.target.files?.[0] || null);
          event.target.value = "";
        }}
      />
    </div>
  );
}
