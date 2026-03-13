import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
};

export function Card({ children, className, ...props }: CardProps) {
  return (
    <section className={cn("card", className)} {...props}>
      {children}
    </section>
  );
}
