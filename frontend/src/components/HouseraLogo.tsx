interface HouseraLogoProps {
  /** Sidebar collapsed — show only the house icon */
  collapsed?: boolean;
  /** Height of the element in px */
  height?: number;
}

// The logo is 640×640.
// House icon occupies roughly the top 58% → ~371px.
// To clip just the icon in a square container we scale the image so
// the icon area exactly fills the container height:
//   scaledSize = containerSize / 0.58
const ICON_RATIO = 0.58;

export function HouseraLogo({ collapsed = false, height = 40 }: HouseraLogoProps) {
  if (collapsed) {
    const scaledSize = Math.round(height / ICON_RATIO);
    return (
      <div style={{
        width: height,
        height: height,
        overflow: 'hidden',
        flexShrink: 0,
      }}>
        <img
          src="/housera-logo.jpeg"
          alt="Housera"
          style={{
            width: scaledSize,
            height: scaledSize,
            display: 'block',
            // Horizontally center; vertically start from top
            marginLeft: `${(height - scaledSize) / 2}px`,
            marginTop: 0,
          }}
        />
      </div>
    );
  }

  // Expanded: full square logo.
  // Show it at `height` size — both icon + "Housera" text visible.
  return (
    <img
      src="/housera-logo.jpeg"
      alt="Housera"
      style={{ height, width: height, display: 'block', flexShrink: 0 }}
    />
  );
}
