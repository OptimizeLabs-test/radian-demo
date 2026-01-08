/**
 * Utility functions for parsing summary content
 */

export interface ParsedSummary {
    headline: string;
    bullets: string[];
  }
  
  /**
   * Parse final summary text into structured format
   * Used when summary streaming is complete
   */
  export function parseSummaryBullets(text: string): ParsedSummary {
    const headlineMatch = text.match(/HEADLINE:\s*(.+?)(?:\n|BULLETS:)/is);
    let headline = headlineMatch?.[1]?.trim() || '';
    if (!headline.startsWith("Overall Status:")) {
      headline = `Overall Status: ${headline}`;
    }
    
    const bullets: string[] = [];
    const bulletsMatch = text.match(/BULLETS:\s*(.+)/is);
    if (bulletsMatch) {
      const lines = bulletsMatch[1].split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.match(/^[-•*]\s+/)) {
          const bulletText = trimmed.replace(/^[-•*]\s+/, "").trim();
          if (bulletText) bullets.push(bulletText);
        }
      }
      
      // Fallback: if the last line lacks a bullet marker but has content, keep it
      const trailing = lines.map(l => l.trim()).filter(Boolean);
      if (trailing.length > 0) {
        const lastLine = trailing[trailing.length - 1];
        const hasMarker = /^[-•*]\s+/.test(lastLine);
        if (!hasMarker && lastLine.length > 0 && !bullets.some(b => b.includes(lastLine))) {
          bullets.push(lastLine);
        }
      }
    }
    
    return { headline, bullets };
  }
  
  /**
   * Parse streaming summary content into headline, completed bullets, and current bullet
   * Used during real-time streaming
   */
  export function parseStreamingSummary(streamedContent: string): { 
    headline: string; 
    parsedBullets: string[]; 
    currentBullet: string;
  } {
    let headline = "";
    const parsedBullets: string[] = [];
    let currentBulletText = "";
  
    // Parse headline
    const headlineMatch = streamedContent.match(/HEADLINE:\s*(.+?)(?:\n|KEY POINTS:)/is);
    if (headlineMatch) {
      headline = headlineMatch[1].trim();
      if (!headline.startsWith("Overall Status:")) {
        headline = `Overall Status: ${headline}`;
      }
    }
  
    // Parse bullets from KEY POINTS section
    const bulletsMatch = streamedContent.match(/KEY POINTS:\s*(.+)/is);
    if (bulletsMatch) {
      const bulletsSection = bulletsMatch[1];
      // Filter out empty lines to avoid double-line rendering issues
      const lines = bulletsSection.split('\n').filter(line => line.trim());
      let tempBulletLines: string[] = [];
  
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmedLine = line.trim();
  
        const isNewBullet = trimmedLine.match(/^[-•*]\s+/) ||
                           (trimmedLine.match(/^\d+\.\s+/) && tempBulletLines.length === 0);
  
        if (isNewBullet) {
          // Save previous bullet if exists
          if (tempBulletLines.length > 0) {
            // Join with single space and clean up extra whitespace
            parsedBullets.push(tempBulletLines.join(" ").replace(/\s+/g, ' ').trim());
            tempBulletLines = [];
          }
          // Start new bullet
          tempBulletLines.push(trimmedLine.replace(/^[-•*]\s+/, "").replace(/^\d+\.\s+/, "").trim());
        } else if (trimmedLine && tempBulletLines.length > 0) {
          // Continue current bullet (multi-line) - add space to join naturally
          tempBulletLines.push(trimmedLine);
        } else if (trimmedLine && tempBulletLines.length === 0) {
          // Text without marker - treat as new bullet
          tempBulletLines.push(trimmedLine);
        }
      }
      
      // Current bullet is what's being built - clean up whitespace
      currentBulletText = tempBulletLines.join(" ").replace(/\s+/g, ' ').trim();
    }
  
    return { headline, parsedBullets, currentBullet: currentBulletText };
  }