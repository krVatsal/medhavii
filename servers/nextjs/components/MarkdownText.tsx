import React from 'react';

interface MarkdownTextProps {
  content: string;
  className?: string;
}

export function MarkdownText({ content, className = '' }: MarkdownTextProps) {
  // Process markdown to HTML
  const processMarkdown = (text: string): string => {
    let html = text;
    
    // Convert **bold** to <strong>
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Convert *italic* to <em>
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Convert `code` to <code>
    html = html.replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">$1</code>');
    
    // Convert [link](url) to <a>
    html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">$1</a>');
    
    // Convert headings (### heading)
    html = html.replace(/^### (.+)$/gm, '<h3 class="font-bold text-base mt-2 mb-1">$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2 class="font-bold text-lg mt-3 mb-1">$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1 class="font-bold text-xl mt-3 mb-2">$1</h1>');
    
    // Convert bullet lists (- item or * item)
    const lines = html.split('\n');
    let inList = false;
    const processedLines: string[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const bulletMatch = line.match(/^[\s]*[-*]\s+(.+)$/);
      
      if (bulletMatch) {
        if (!inList) {
          processedLines.push('<ul class="list-disc pl-5 space-y-1 my-2">');
          inList = true;
        }
        processedLines.push(`<li>${bulletMatch[1]}</li>`);
      } else {
        if (inList) {
          processedLines.push('</ul>');
          inList = false;
        }
        processedLines.push(line);
      }
    }
    
    if (inList) {
      processedLines.push('</ul>');
    }
    
    html = processedLines.join('\n');
    
    // Convert numbered lists (1. item)
    html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<li class="ml-5">$2</li>');
    
    // Convert line breaks (double newline to <br>)
    html = html.replace(/\n\n/g, '<br /><br />');
    html = html.replace(/\n/g, '<br />');
    
    return html;
  };

  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: processMarkdown(content) }}
    />
  );
}
