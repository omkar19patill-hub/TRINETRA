import AnimatedGradient from "./AnimatedGradient";

// Module-level on purpose. A config object created inside a component is a new object on
// every render, and AnimatedGradient rebuilds its WebGL program whenever `config` changes
// (tested: 13 rebuilds in 2.5s vs 1). Keep this constant.
const BACKGROUND_CONFIG = { preset: "Prism" } as const;

const GRADIENT_STYLE = { position: "absolute", zIndex: 0 } as const;

/**
 * Site-wide animated background. Mount ONCE, near the app root, so it survives route changes.
 * Fixed, behind all content, never intercepts clicks, hidden from assistive tech.
 * The #050505 backing colour is what shows if WebGL2 is unavailable.
 */
export default function AppBackground() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: -1,
        pointerEvents: "none",
        backgroundColor: "#050505",
      }}
    >
      <AnimatedGradient config={BACKGROUND_CONFIG} style={GRADIENT_STYLE} />
    </div>
  );
}
