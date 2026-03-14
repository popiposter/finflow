import { cn } from "@/shared/lib/utils";

type SkeletonProps = {
  variant?: "text" | "heading" | "metric" | "card" | "chart" | "avatar";
  className?: string;
  width?: string;
};

export function Skeleton({ variant = "text", className, width }: SkeletonProps) {
  return (
    <div
      className={cn("skeleton", `skeleton--${variant}`, className)}
      style={width ? { width } : undefined}
      aria-hidden="true"
    />
  );
}

export function SkeletonRows({ count = 3 }: { count?: number }) {
  return (
    <div style={{ display: "grid", gap: "0.75rem" }}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} style={{ display: "grid", gap: "0.35rem" }}>
          <Skeleton variant="text" width={i === 0 ? "80%" : i === 1 ? "60%" : "70%"} />
          <Skeleton variant="text" width="40%" />
        </div>
      ))}
    </div>
  );
}
