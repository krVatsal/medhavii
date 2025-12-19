"use client";

import React, { useEffect, useRef } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface LaTeXRendererProps {
  content: string;
  className?: string;
}

/**
 * Renders text with LaTeX math formulas using KaTeX
 * Supports:
 * - Inline math: $...$ or \(...\)
 * - Display math: $$...$$ or \[...\]
 */
const LaTeXRenderer: React.FC<LaTeXRendererProps> = ({ content, className = '' }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !content) return;

    try {
      let html = content;

      // Convert common programming-style math notation to LaTeX
      // sqrt(x) -> \sqrt{x}
      html = html.replace(/sqrt\(([^)]+)\)/g, '\\sqrt{$1}');
      // x^2 -> x^{2} (wrap exponents in braces)
      html = html.replace(/\^([0-9]+)/g, '^{$1}');

      // Replace LaTeX environments (matrix, equation, align, etc.) - must be FIRST
      html = html.replace(/\\begin\{(matrix|pmatrix|bmatrix|vmatrix|Vmatrix|equation|align|array|cases)\}([\s\S]*?)\\end\{\1\}/g, (match, env, formula) => {
        try {
          // Fix common LaTeX errors: single backslash line breaks -> double backslash
          // Replace " \ " with " \\ " (single backslash between spaces/content -> double)
          let fixedFormula = formula.replace(/([^\\])\s*\\\s+(?=[^\s\\])/g, '$1 \\\\ ');
          
          // For environments, we need to keep the \begin and \end tags for KaTeX
          const fullFormula = `\\begin{${env}}${fixedFormula}\\end{${env}}`;
          return katex.renderToString(fullFormula, {
            displayMode: true,
            throwOnError: false,
          });
        } catch (e) {
          console.error('LaTeX environment rendering error:', e);
          return match;
        }
      });

      // Replace display math $$...$$ (before inline to avoid conflicts)
      html = html.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
        try {
          return katex.renderToString(formula.trim(), {
            displayMode: true,
            throwOnError: false,
          });
        } catch (e) {
          return match; // Return original if rendering fails
        }
      });

      // Replace display math \[...\]
      html = html.replace(/\\\[([\s\S]+?)\\\]/g, (match, formula) => {
        try {
          return katex.renderToString(formula.trim(), {
            displayMode: true,
            throwOnError: false,
          });
        } catch (e) {
          return match;
        }
      });

      // Replace inline math $...$
      html = html.replace(/\$([^\$\n]+?)\$/g, (match, formula) => {
        try {
          return katex.renderToString(formula.trim(), {
            displayMode: false,
            throwOnError: false,
          });
        } catch (e) {
          return match;
        }
      });

      // Replace inline math \(...\)
      html = html.replace(/\\\(([^\)]+?)\\\)/g, (match, formula) => {
        try {
          return katex.renderToString(formula.trim(), {
            displayMode: false,
            throwOnError: false,
          });
        } catch (e) {
          return match;
        }
      });

      containerRef.current.innerHTML = html;
    } catch (error) {
      console.error('LaTeX rendering error:', error);
      if (containerRef.current) {
        containerRef.current.textContent = content; // Fallback to plain text
      }
    }
  }, [content]);

  return <div ref={containerRef} className={className} />;
};

export default LaTeXRenderer;
