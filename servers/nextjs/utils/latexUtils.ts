/**
 * Utility functions for handling LaTeX in text
 */

/**
 * Check if a string contains LaTeX math notation
 */
export function containsLaTeX(text: string): boolean {
  if (!text) return false;
  
  // Check for common LaTeX delimiters
  const patterns = [
    /\$\$[\s\S]+?\$\$/,  // Display math: $$...$$
    /\\\[[\s\S]+?\\\]/,   // Display math: \[...\]
    /\$[^\$\n]+?\$/,      // Inline math: $...$
    /\\\([^\)]+?\\\)/,    // Inline math: \(...\)
    /\\begin\{(matrix|pmatrix|bmatrix|vmatrix|Vmatrix|equation|align|array|cases)\}/,  // LaTeX environments
    /\\end\{(matrix|pmatrix|bmatrix|vmatrix|Vmatrix|equation|align|array|cases)\}/,    // LaTeX environment ends
    /\\(frac|sqrt|sum|int|lim|sin|cos|tan|log|ln|exp|alpha|beta|gamma|theta|pi|infty|partial|nabla|times|cdot|pm|leq|geq|neq|approx)\{?/  // Common LaTeX commands
  ];
  
  return patterns.some(pattern => pattern.test(text));
}

/**
 * Extract plain text from LaTeX (for fallback display)
 */
export function stripLaTeX(text: string): string {
  if (!text) return '';
  
  let result = text;
  
  // Remove display math delimiters
  result = result.replace(/\$\$([\s\S]+?)\$\$/g, '$1');
  result = result.replace(/\\\[([\s\S]+?)\\\]/g, '$1');
  
  // Remove inline math delimiters  
  result = result.replace(/\$([^\$\n]+?)\$/g, '$1');
  result = result.replace(/\\\(([^\)]+?)\\\)/g, '$1');
  
  // Convert common LaTeX commands to readable text
  result = result.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1)/($2)');
  result = result.replace(/\\sqrt\{([^}]+)\}/g, '√($1)');
  result = result.replace(/\\([a-zA-Z]+)\{([^}]+)\}/g, '$2'); // Generic command{arg}
  result = result.replace(/\\([a-zA-Z]+)/g, '$1'); // Generic \command
  result = result.replace(/[{}]/g, ''); // Remove remaining braces
  
  return result.trim();
}
