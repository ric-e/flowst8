import { cn } from '@/lib/utils';
export function Separator({ className }: { className?: string }) {
  return <hr className={cn('border-neutral-800', className)} />;
}
