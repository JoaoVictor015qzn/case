export function MissingList({ missing }: { missing: string[] }) {
  if (missing.length === 0) return null;
  return (
    <div className="missing">
      <strong>Não atendido</strong>
      <ul>
        {missing.map((entry) => (
          <li key={entry}>{entry}</li>
        ))}
      </ul>
    </div>
  );
}
