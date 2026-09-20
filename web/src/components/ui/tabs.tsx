import * as React from "react";
import { cn } from "@/lib/utils";

interface TabsContextValue {
  value: string;
  onValueChange: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | undefined>(undefined);

export function Tabs({
  value,
  onValueChange,
  defaultValue,
  children,
  className,
}: {
  value?: string;
  onValueChange?: (value: string) => void;
  defaultValue?: string;
  children: React.ReactNode;
  className?: string;
}) {
  const [currentValue, setCurrentValue] = React.useState(defaultValue || '');
  const activeValue = value !== undefined ? value : currentValue;
  const handleValueChange = onValueChange || setCurrentValue;

  return (
    <TabsContext.Provider value={{ value: activeValue, onValueChange: handleValueChange }}>
      <div className={cn("flex flex-col space-y-2", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <div
      className={cn(
        "inline-flex h-9 items-center justify-start rounded-lg bg-secondary/60 p-1 text-muted-foreground overflow-x-auto max-w-full",
        className
      )}
    >
      {children}
    </div>
  );
}

export function TabsTrigger({
  value,
  className,
  children,
  badge,
}: {
  value: string;
  className?: string;
  children: React.ReactNode;
  badge?: number | string;
}) {
  const context = React.useContext(TabsContext);
  if (!context) throw new Error("TabsTrigger must be used within Tabs");

  const isActive = context.value === value;

  return (
    <button
      type="button"
      onClick={() => context.onValueChange(value)}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1 text-xs font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 cursor-pointer gap-1.5",
        isActive
          ? "bg-background text-foreground shadow-sm font-semibold"
          : "hover:bg-background/40 hover:text-foreground text-muted-foreground",
        className
      )}
    >
      {children}
      {badge !== undefined && (
        <span
          className={cn(
            "ml-1 rounded-full px-1.5 py-0.2 text-[10px]",
            isActive ? "bg-primary/20 text-primary font-bold" : "bg-muted text-muted-foreground"
          )}
        >
          {badge}
        </span>
      )}
    </button>
  );
}

export function TabsContent({
  value,
  className,
  children,
}: {
  value: string;
  className?: string;
  children: React.ReactNode;
}) {
  const context = React.useContext(TabsContext);
  if (!context) throw new Error("TabsContent must be used within Tabs");

  if (context.value !== value) return null;

  return (
    <div
      className={cn(
        "ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 animate-in fade-in-50 duration-150",
        className
      )}
    >
      {children}
    </div>
  );
}
