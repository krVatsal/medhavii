"use client";

import React from 'react';
import LaTeXRenderer from '@/components/LaTeXRenderer';
import { containsLaTeX } from '@/utils/latexUtils';

interface TextWithLaTeXProps {
  content: string;
  className?: string;
  as?: 'p' | 'span' | 'div' | 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
  style?: React.CSSProperties;
  dangerouslySetInnerHTML?: { __html: string };
}

/**
 * Smart text component that renders LaTeX if present, otherwise renders as normal HTML
 * Can be used as a drop-in replacement for text elements in presentation templates
 */
const TextWithLaTeX: React.FC<TextWithLaTeXProps> = ({ 
  content, 
  className = '', 
  as: Component = 'div',
  style,
  dangerouslySetInnerHTML
}) => {
  // If dangerouslySetInnerHTML is provided, check that HTML for LaTeX
  const htmlContent = dangerouslySetInnerHTML?.__html || content;
  
  // Check if content contains LaTeX
  if (containsLaTeX(htmlContent)) {
    return <LaTeXRenderer content={htmlContent} className={className} />;
  }
  
  // No LaTeX, render normally
  if (dangerouslySetInnerHTML) {
    return <Component className={className} style={style} dangerouslySetInnerHTML={dangerouslySetInnerHTML} />;
  }
  
  return <Component className={className} style={style}>{content}</Component>;
};

export default TextWithLaTeX;
