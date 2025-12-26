import { useEffect } from 'react';

/**
 * Custom hook to set the document title dynamically
 * @param title - The page-specific title (e.g., "Dashboard", "Group Name")
 * @param prefix - Optional prefix (defaults to "Splitwiser")
 */
export const usePageTitle = (title: string, prefix: string = 'Splitwiser') => {
  useEffect(() => {
    const previousTitle = document.title;

    // Set the new title
    document.title = title ? `${prefix} - ${title}` : prefix;

    // Cleanup: restore previous title on unmount (optional)
    return () => {
      document.title = previousTitle;
    };
  }, [title, prefix]);
};
