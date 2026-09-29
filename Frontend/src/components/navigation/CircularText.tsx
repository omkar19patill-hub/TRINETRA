// Originkit Text Ring / CircularText component
"use client";

import * as React from "react";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  animate,
  motion,
  useAnimationFrame,
  useMotionValue,
  type AnimationPlaybackControls,
} from "framer-motion";

type FontStyle = React.CSSProperties & {
  fontFamily?: string;
  fontWeight?: number | string;
  fontSize?: number | string;
  letterSpacing?: number | string;
};

type HoverEffect = "speed" | "pause" | "scale";

type TransitionValue = {
  type?: string;
  duration?: number;
  delay?: number;
  ease?: string | number[];
  mass?: number;
  damping?: number;
  stiffness?: number;
  [key: string]: unknown;
};

export type CircularTextProps = {
  words?: string[];
  separator?: string;
  diameter?: number;
  font?: FontStyle;
  color?: string;
  onHover?: HoverEffect;
  hoverScale?: number;
  /** Seconds per full rotation on hover (1–8). */
  hoverSpeed?: number;
  transition?: TransitionValue;
  style?: React.CSSProperties;
  className?: string;
};

const MAX_WORDS = 10;
const DEFAULT_WORDS = ["CIRCULAR", "TEXT"];
const DEFAULT_SEPARATOR = "⁕";
const DEFAULT_DIAMETER = 320;
const MIN_LETTER_SPACING = 0;

const DEFAULT_TRANSITION: TransitionValue = {
  type: "tween",
  duration: 20,
  delay: 0,
  ease: "linear",
};

const DEFAULT_FONT: FontStyle = {
  fontFamily: "Inter",
  fontWeight: 400,
  fontSize: "24px",
  letterSpacing: "0.02em",
  lineHeight: "1em",
  textAlign: "center",
};

type Size = { width: number; height: number };

const resolveSpinDuration = (transition: TransitionValue | undefined): number => {
  const duration = transition?.duration ?? DEFAULT_TRANSITION.duration ?? 20;
  return Number.isFinite(duration) && duration > 0 ? duration : 0;
};

const resolveSpinDelay = (transition: TransitionValue | undefined): number => {
  const delay = transition?.delay ?? 0;
  return Number.isFinite(delay) && delay > 0 ? delay : 0;
};

/** Degrees per second for a full lap in `durationSec`. */
const degreesPerSecond = (durationSec: number): number => {
  if (!Number.isFinite(durationSec) || durationSec <= 0) return 0;
  return 360 / durationSec;
};

const resolveHoverDuration = (hoverSpeed: number | undefined): number => {
  if (!Number.isFinite(hoverSpeed)) return 5;
  return Math.min(8, Math.max(1, hoverSpeed as number));
};

const prefersReducedMotion = (): boolean => {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
};

const parseFontSizePx = (fontSize: FontStyle["fontSize"]): number => {
  if (typeof fontSize === "number") return fontSize;
  if (typeof fontSize === "string" && fontSize.length > 0) {
    const parsed = Number.parseFloat(fontSize);
    if (Number.isFinite(parsed)) return parsed;
  }
  return 24;
};

const parseLetterSpacingPx = (
  letterSpacing: FontStyle["letterSpacing"],
  fontSizePx: number
): number => {
  if (typeof letterSpacing === "number") return letterSpacing;
  if (typeof letterSpacing !== "string" || letterSpacing.length === 0) return 0;

  if (letterSpacing.endsWith("em")) {
    const em = Number.parseFloat(letterSpacing);
    return Number.isFinite(em) ? em * fontSizePx : 0;
  }

  const parsed = Number.parseFloat(letterSpacing);
  return Number.isFinite(parsed) ? parsed : 0;
};

const parseFontWeight = (fontWeight: FontStyle["fontWeight"]): string => {
  if (typeof fontWeight === "number") return String(fontWeight);
  if (typeof fontWeight === "string" && fontWeight.length > 0) return fontWeight;
  return "900";
};

const parseFontFamily = (fontFamily: FontStyle["fontFamily"]): string => {
  if (typeof fontFamily === "string" && fontFamily.length > 0) {
    return fontFamily.split(",")[0]?.trim().replace(/['"]/g, "") || "sans-serif";
  }
  return "sans-serif";
};

const cleanWords = (words: string[] | undefined): string[] => {
  const cleaned = (words ?? [])
    .map((word) => word.trim())
    .filter(Boolean)
    .slice(0, MAX_WORDS);
  return cleaned.length > 0 ? cleaned : DEFAULT_WORDS;
};

/** One lap segment ending with a separator so repeats tile cleanly. */
const buildSegment = (words: string[], separator: string): string => {
  const glyph =
    (separator && separator.length > 0 ? separator : DEFAULT_SEPARATOR).trim() ||
    DEFAULT_SEPARATOR;
  return `${words.join(` ${glyph} `)} ${glyph} `;
};

const measureGlyphWidths = (
  letters: string[],
  fontSizePx: number,
  fontWeight: string,
  fontFamily: string
): number[] => {
  if (letters.length === 0) return [];

  if (typeof document === "undefined") {
    return letters.map((letter) =>
      letter === " " ? fontSizePx * 0.35 : fontSizePx * 0.55
    );
  }

  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  if (!context) {
    return letters.map((letter) =>
      letter === " " ? fontSizePx * 0.35 : fontSizePx * 0.55
    );
  }

  context.font = `${fontWeight} ${fontSizePx}px ${fontFamily}`;
  return letters.map((letter) => {
    const glyph = letter === " " ? "\u00A0" : letter;
    return context.measureText(glyph).width;
  });
};

const measureGlyphWidth = (
  letters: string[],
  fontSizePx: number,
  fontWeight: string,
  fontFamily: string
): number => {
  const widths = measureGlyphWidths(letters, fontSizePx, fontWeight, fontFamily);
  return widths.reduce((sum, width) => sum + width, 0);
};

const measureArcLength = (
  letters: string[],
  fontSizePx: number,
  fontWeight: string,
  fontFamily: string,
  letterSpacingPx: number
): number => {
  if (letters.length === 0) return 0;
  return (
    measureGlyphWidth(letters, fontSizePx, fontWeight, fontFamily) +
    letterSpacingPx * letters.length
  );
};

/**
 * Build letter list + spacing so text covers the circumference.
 * Font letter-spacing is the minimum gap — only compressed when one lap can't fit.
 * Short words are repeated to fill; spacing then expands to cover the ring.
 */
const buildFittedCircleText = (
  words: string[],
  separator: string,
  circumference: number,
  fontSizePx: number,
  fontWeight: string,
  fontFamily: string,
  preferredLetterSpacing: number
): {
  letters: string[];
  letterSpacingPx: number;
  content: string;
  angles: number[];
} => {
  const preferred = Math.max(MIN_LETTER_SPACING, preferredLetterSpacing);
  const segment = buildSegment(words, separator);
  const segmentLetters = Array.from(segment);

  if (segmentLetters.length === 0 || circumference <= 0) {
    return {
      letters: [],
      letterSpacingPx: preferred,
      content: "",
      angles: [],
    };
  }

  const segmentAtPreferred = measureArcLength(
    segmentLetters,
    fontSizePx,
    fontWeight,
    fontFamily,
    preferred
  );

  let repeats = Math.max(1, Math.ceil(circumference / Math.max(segmentAtPreferred, 1)));
  repeats = Math.min(repeats, 48);

  const solveSpacing = (glyphTotal: number, count: number): number => {
    if (count <= 0) return preferred;
    return (circumference - glyphTotal) / count;
  };

  let content = segment.repeat(repeats);
  let letters = Array.from(content);
  let glyphWidth = measureGlyphWidth(letters, fontSizePx, fontWeight, fontFamily);
  let letterSpacingPx = solveSpacing(glyphWidth, letters.length);

  while (letterSpacingPx < preferred && repeats > 1) {
    repeats -= 1;
    content = segment.repeat(repeats);
    letters = Array.from(content);
    glyphWidth = measureGlyphWidth(letters, fontSizePx, fontWeight, fontFamily);
    letterSpacingPx = solveSpacing(glyphWidth, letters.length);
  }

  if (letterSpacingPx < preferred) {
    letterSpacingPx = Math.max(MIN_LETTER_SPACING, letterSpacingPx);
  }

  const stretchLimit = Math.max(preferred * 2.5, fontSizePx * 0.75);
  while (letterSpacingPx > stretchLimit && repeats < 48) {
    const nextRepeats = repeats + 1;
    const nextContent = segment.repeat(nextRepeats);
    const nextLetters = Array.from(nextContent);
    const nextGlyphs = measureGlyphWidth(nextLetters, fontSizePx, fontWeight, fontFamily);
    const nextSpacing = solveSpacing(nextGlyphs, nextLetters.length);
    if (nextSpacing < preferred) break;
    repeats = nextRepeats;
    content = nextContent;
    letters = nextLetters;
    glyphWidth = nextGlyphs;
    letterSpacingPx = nextSpacing;
  }

  const widths = measureGlyphWidths(letters, fontSizePx, fontWeight, fontFamily);
  const totalArc =
    widths.reduce((sum, width) => sum + width, 0) + letterSpacingPx * letters.length;

  const angles: number[] = [];
  let cursor = 0;
  for (let i = 0; i < letters.length; i += 1) {
    const width = widths[i] ?? 0;
    const center = cursor + width / 2;
    angles.push(totalArc > 0 ? (center / totalArc) * 360 : 0);
    cursor += width + letterSpacingPx;
  }

  return { letters, letterSpacingPx, content, angles };
};

const DEFAULT_PROPS: Required<Omit<CircularTextProps, "style" | "className">> = {
  words: DEFAULT_WORDS,
  separator: DEFAULT_SEPARATOR,
  diameter: DEFAULT_DIAMETER,
  font: DEFAULT_FONT,
  color: "#FFFFFF",
  onHover: "speed",
  hoverScale: 0.8,
  hoverSpeed: 5,
  transition: DEFAULT_TRANSITION,
};

function OriginkitBaseCircularText(props: CircularTextProps) {
  const {
    words = DEFAULT_PROPS.words,
    separator = DEFAULT_PROPS.separator,
    diameter = DEFAULT_PROPS.diameter,
    font = DEFAULT_PROPS.font,
    color = DEFAULT_PROPS.color,
    onHover = DEFAULT_PROPS.onHover,
    hoverScale = DEFAULT_PROPS.hoverScale,
    hoverSpeed = DEFAULT_PROPS.hoverSpeed,
    transition = DEFAULT_PROPS.transition,
    style,
    className = "",
  } = props;

  const frameRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<Size>({
    width: diameter,
    height: diameter,
  });

  const rotation = useMotionValue(0);
  const scale = useMotionValue(1);
  const spinRateRef = useRef(0);
  const pausedRef = useRef(false);
  const delayUntilRef = useRef(0);
  const scaleAnimRef = useRef<AnimationPlaybackControls | null>(null);

  const spinDuration = resolveSpinDuration(transition);
  const spinDelay = resolveSpinDelay(transition);

  const fontSizePx = parseFontSizePx(font?.fontSize);
  const preferredLetterSpacing = parseLetterSpacingPx(font?.letterSpacing, fontSizePx);
  const fontWeight = parseFontWeight(font?.fontWeight);
  const fontFamily = parseFontFamily(font?.fontFamily);

  const safeDiameter = Math.max(10, diameter);

  useLayoutEffect(() => {
    const node = frameRef.current;
    if (!node) return;

    const updateSize = (width: number, height: number) => {
      const nextWidth = Math.max(0, Math.floor(width));
      const nextHeight = Math.max(0, Math.floor(height));
      setSize((prev) => {
        if (prev.width === nextWidth && prev.height === nextHeight) return prev;
        if (nextWidth < 2 || nextHeight < 2) {
          return { width: safeDiameter, height: safeDiameter };
        }
        return { width: nextWidth, height: nextHeight };
      });
    };

    updateSize(node.clientWidth, node.clientHeight);

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      updateSize(entry.contentRect.width, entry.contentRect.height);
    });

    observer.observe(node);
    return () => observer.disconnect();
  }, [safeDiameter]);

  const maxFrameSize = Math.max(0, Math.min(size.width, size.height));
  const ringSize = maxFrameSize > 0 ? Math.min(safeDiameter, maxFrameSize) : safeDiameter;
  const radius = Math.max(8, ringSize / 2 - fontSizePx * 0.55);
  const circumference = 2 * Math.PI * radius;

  const wordList = useMemo(() => cleanWords(words), [words]);

  const fitted = useMemo(
    () =>
      buildFittedCircleText(
        wordList,
        separator,
        circumference,
        fontSizePx,
        fontWeight,
        fontFamily,
        preferredLetterSpacing
      ),
    [wordList, separator, circumference, fontSizePx, fontWeight, fontFamily, preferredLetterSpacing]
  );

  const { letters, letterSpacingPx, content, angles } = fitted;

  useEffect(() => {
    if (prefersReducedMotion() || spinDuration <= 0) {
      spinRateRef.current = 0;
      pausedRef.current = true;
      delayUntilRef.current = 0;
      scaleAnimRef.current?.stop();
      scale.set(1);
      return;
    }

    pausedRef.current = false;
    spinRateRef.current = degreesPerSecond(spinDuration);
    delayUntilRef.current = spinDelay > 0 ? performance.now() + spinDelay * 1000 : 0;
    scaleAnimRef.current?.stop();
    scale.set(1);
  }, [spinDuration, spinDelay, content, onHover, scale]);

  useAnimationFrame((_, delta) => {
    if (pausedRef.current || spinRateRef.current === 0) return;
    if (delayUntilRef.current > 0 && performance.now() < delayUntilRef.current) {
      return;
    }
    delayUntilRef.current = 0;

    const dt = Math.min(delta, 64) / 1000;
    const next = (rotation.get() + spinRateRef.current * dt) % 360;
    rotation.set(next < 0 ? next + 360 : next);
  });

  useEffect(() => {
    return () => {
      scaleAnimRef.current?.stop();
    };
  }, []);

  const animateScale = (target: number) => {
    scaleAnimRef.current?.stop();
    scaleAnimRef.current = animate(scale, target, {
      type: "spring",
      damping: 20,
      stiffness: 300,
    });
  };

  const handleHoverStart = () => {
    if (prefersReducedMotion() || !onHover || spinDuration <= 0) return;

    const hoverDurationSec = resolveHoverDuration(hoverSpeed);

    switch (onHover) {
      case "speed": {
        pausedRef.current = false;
        spinRateRef.current = degreesPerSecond(hoverDurationSec);
        animateScale(1);
        break;
      }
      case "pause": {
        pausedRef.current = true;
        animateScale(1);
        break;
      }
      case "scale": {
        pausedRef.current = false;
        spinRateRef.current = degreesPerSecond(hoverDurationSec);
        const nextScale = Number.isFinite(hoverScale) ? hoverScale : 0.8;
        animateScale(nextScale);
        break;
      }
      default:
        pausedRef.current = false;
        spinRateRef.current = degreesPerSecond(spinDuration);
        animateScale(1);
    }
  };

  const handleHoverEnd = () => {
    if (prefersReducedMotion() || spinDuration <= 0) return;

    pausedRef.current = false;
    spinRateRef.current = degreesPerSecond(spinDuration);
    animateScale(1);
  };

  return (
    <div
      ref={frameRef}
      className={className}
      style={{
        width: "100%",
        height: "100%",
        minWidth: safeDiameter,
        minHeight: safeDiameter,
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        ...style,
      }}
    >
      <div
        onPointerEnter={handleHoverStart}
        onPointerLeave={handleHoverEnd}
        style={{
          position: "relative",
          width: ringSize,
          height: ringSize,
          flexShrink: 0,
          borderRadius: "50%",
          cursor: "pointer",
          touchAction: "manipulation",
          userSelect: "none",
        }}
      >
        <motion.div
          style={{
            ...font,
            letterSpacing: `${letterSpacingPx}px`,
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            borderRadius: "50%",
            color,
            textAlign: "center",
            transformOrigin: "center center",
            willChange: "transform",
            pointerEvents: "none",
            rotate: rotation,
            scale,
          }}
        >
          {letters.map((letter, i) => {
            const angle = angles[i] ?? 0;
            const rad = (angle * Math.PI) / 180;
            const x = radius * Math.cos(rad);
            const y = radius * Math.sin(rad);
            const transform = `translate(-50%, -50%) translate(${x}px, ${y}px) rotate(${angle + 90}deg)`;

            return (
              <span
                key={`${letter}-${i}`}
                aria-hidden="true"
                style={{
                  position: "absolute",
                  top: "50%",
                  left: "50%",
                  display: "inline-block",
                  lineHeight: 1,
                  transform,
                  WebkitTransform: transform,
                }}
              >
                {letter === " " ? "\u00A0" : letter}
              </span>
            );
          })}

          <span
            style={{
              position: "absolute",
              width: 1,
              height: 1,
              padding: 0,
              margin: -1,
              overflow: "hidden",
              clip: "rect(0, 0, 0, 0)",
              whiteSpace: "nowrap",
              borderWidth: 0,
            }}
          >
            {content}
          </span>
        </motion.div>
      </div>
    </div>
  );
}

const TRINETRA_TEXT_RING_PRESET: CircularTextProps = {
  font: {
    fontSize: "24px",
    textAlign: "center",
    fontFamily: "Inter",
    fontWeight: 700,
    lineHeight: "1em",
    letterSpacing: "0.02em",
  },
  color: "#FFFFFF",
  words: ["TRINETRA"],
  onHover: "speed",
  diameter: 320,
  separator: "⁕",
  hoverScale: 0.8,
  hoverSpeed: 8,
  transition: {
    ease: "linear",
    mass: 1,
    type: "tween",
    delay: 0,
    damping: 60,
    duration: 20,
    stiffness: 800,
  },
};

export default function CircularText(props: CircularTextProps) {
  return <OriginkitBaseCircularText {...TRINETRA_TEXT_RING_PRESET} {...props} />;
}
