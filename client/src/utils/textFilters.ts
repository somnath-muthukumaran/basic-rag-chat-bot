/**
 * Utility functions for filtering and processing text content
 */

/**
 * Process text with thinking tags and return appropriate display content
 * @param text The text to process
 * @returns Object with display text and thinking status
 */
export function processThinkingText(text: string): { displayText: string; isThinking: boolean } {
  // Check if text contains an open think tag without a close tag (still thinking)
  const hasOpenThink = /<think>/i.test(text) && !/<\/think>/i.test(text);
  
  // Check if text is currently inside a think block
  const thinkMatch = text.match(/<think>([\s\S]*?)(?:<\/think>|$)/i);
  
  if (hasOpenThink || (thinkMatch && !text.includes('</think>'))) {
    // Model is currently thinking
    return { displayText: "🤔 Thinking...", isThinking: true };
  }
  
  // Remove completed think blocks and return clean text
  const cleanText = text.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
  
  return { displayText: cleanText, isThinking: false };
}

/**
 * Remove <think>...</think> tags and their content from text
 * @param text The text to filter
 * @returns Filtered text without thinking content
 */
export function removeThinkTags(text: string): string {
  return text.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
}

/**
 * Clean and normalize text content
 * @param text The text to clean
 * @returns Cleaned text
 */
export function cleanText(text: string): string {
  return removeThinkTags(text)
    .replace(/\s+/g, ' ') // Replace multiple whitespace with single space
    .trim();
}
