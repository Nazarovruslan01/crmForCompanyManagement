export function LoadingSpinner() {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--color-gray-7)',
        fontSize: 14,
      }}
    >
      Загрузка...
    </div>
  );
}
