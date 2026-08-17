import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const setTheme = vi.fn();

vi.mock('next-themes', () => ({
  useTheme: () => ({ resolvedTheme: 'light', setTheme }),
}));

import { ThemeToggle } from '@/components/theme-toggle';

describe('ThemeToggle', () => {
  it('switches to dark mode when clicked from light mode', () => {
    render(<ThemeToggle />);

    fireEvent.click(screen.getByRole('button', { name: /toggle color theme/i }));

    expect(setTheme).toHaveBeenCalledWith('dark');
  });
});
