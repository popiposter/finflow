import { motion } from "framer-motion";
import type { ReactNode } from "react";

type AnimatedListProps = {
  children: ReactNode;
  className?: string;
};

const container = {
  animate: {
    transition: {
      staggerChildren: 0.04,
    },
  },
};

const item = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
};

export function AnimatedList({ children, className }: AnimatedListProps) {
  return (
    <motion.div
      className={className}
      variants={container}
      initial="initial"
      animate="animate"
    >
      {children}
    </motion.div>
  );
}

export function AnimatedListItem({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <motion.div
      className={className}
      variants={item}
      transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  );
}
