import ReactMarkdown from 'react-markdown';

interface StructuredMessageProps {
  content: string;
  isUser: boolean;
}

/**
 * Parses markdown content and renders it with better visual hierarchy:
 * - Sections are rendered as separate cards
 * - Lists are more spaced out
 * - Follow-up questions are extracted into CTA bubbles
 */
export default function StructuredMessage({ content }: StructuredMessageProps) {
  // Extract follow-up questions (look for patterns at the end)
  const followUpPatterns = [
    /Would you like me to[^.]*[?.]/gi,
    /Need more help[^.]*[?.]/gi,
    /Would you like[^.]*[?.]/gi,
    /Can I help[^.]*[?.]/gi,
    /Want me to[^.]*[?.]/gi,
    /Would you like to[^.]*[?.]/gi,
  ];

  let mainContent = content;
  let followUpQuestion: string | null = null;

  // Look for follow-up question near the end (last 400 chars)
  const lastPart = content.slice(-400);
  for (const pattern of followUpPatterns) {
    const matches = lastPart.match(pattern);
    if (matches && matches.length > 0) {
      const question = matches[matches.length - 1].trim();
      const questionIndex = content.lastIndexOf(question);
      
      // Extract if found in the last part
      if (questionIndex > content.length - 400) {
        followUpQuestion = question;
        mainContent = content.substring(0, questionIndex).trim();
        
        // Remove common prefixes/suffixes
        mainContent = mainContent.replace(/\n\n---\n\n?$/, '');
        break;
      }
    }
  }

  // Split content into sections
  const sections = parseSections(mainContent);

  return (
    <div className="space-y-5">
      {/* Main content sections */}
      {sections.map((section, idx) => (
        <MessageSection key={idx} section={section} />
      ))}
      
      {/* Follow-up question in CTA bubble */}
      {followUpQuestion && (
        <FollowUpCTA question={followUpQuestion} />
      )}
    </div>
  );
}

interface Section {
  title?: string;
  content: string;
  level: number;
}

function parseSections(content: string): Section[] {
  const sections: Section[] = [];
  
  // First, try to split by markdown headers (## or ###)
  const headerRegex = /^(#{2,3})\s+(.+)$/gm;
  const headerMatches = Array.from(content.matchAll(headerRegex));
  
  if (headerMatches.length > 0) {
    // Has headers - split by them
    let lastIndex = 0;
    
    headerMatches.forEach((match, idx) => {
      const matchIndex = match.index || 0;
      const level = match[1].length;
      const title = match[2].trim();
      
      // Save content before this header (if any)
      if (matchIndex > lastIndex) {
        const prevContent = content.substring(lastIndex, matchIndex).trim();
        if (prevContent) {
          sections.push({
            content: prevContent,
            level: 0,
          });
        }
      }
      
      // Find next header or end of content
      const nextMatch = headerMatches[idx + 1];
      const nextIndex = nextMatch ? (nextMatch.index || content.length) : content.length;
      const sectionContent = content.substring(matchIndex + match[0].length, nextIndex).trim();
      
      sections.push({
        title,
        content: sectionContent,
        level,
      });
      
      lastIndex = nextIndex;
    });
  } else {
    // No headers - try to detect sections by patterns (OUTBOUND, RETURN, DATE NIGHT, etc.)
    const sectionPatterns = [
      /(OUTBOUND|DEPARTURE|DEPARTING).*?FLIGHT/gi,
      /(RETURN|RETURNING).*?FLIGHT/gi,
      /(DATE|RESTAURANT|DINING).*?(NIGHT|SPOT|OPTION)/gi,
      /(ACTION|NEXT|RECOMMENDATION).*?(ITEM|STEP)/gi,
    ];
    
    let hasDetectedSections = false;
    
    // Simple approach: if content is long, split by double newlines
    const paragraphs = content.split(/\n\n+/).filter(p => p.trim());
    
    if (paragraphs.length > 3) {
      // Group related paragraphs
      let currentSection: Section | null = null;
      
      for (const para of paragraphs) {
        // Check if paragraph starts with a section indicator
        const isSectionHeader = sectionPatterns.some(pattern => pattern.test(para.split('\n')[0]));
        
        if (isSectionHeader && currentSection) {
          sections.push(currentSection);
          currentSection = null;
        }
        
        if (!currentSection) {
          currentSection = {
            content: para,
            level: 0,
          };
          hasDetectedSections = true;
        } else {
          currentSection.content += '\n\n' + para;
        }
      }
      
      if (currentSection) {
        sections.push(currentSection);
      }
    }
    
    // If no sections detected, return as single section
    if (!hasDetectedSections || sections.length === 0) {
      sections.push({
        content,
        level: 0,
      });
    }
  }
  
  return sections;
}

function MessageSection({ section }: { section: Section }) {
  const hasTitle = section.title && section.level > 0;
  const titleLower = section.title?.toLowerCase() || '';
  const contentLower = section.content.toLowerCase();
  
  const isFlightSection = titleLower.includes('flight') || 
                         titleLower.includes('outbound') || 
                         titleLower.includes('return') ||
                         titleLower.includes('departure');
  
  const isRestaurantSection = titleLower.includes('restaurant') || 
                             titleLower.includes('date') ||
                             titleLower.includes('dining') ||
                             titleLower.includes('spot') ||
                             contentLower.includes('restaurant') && contentLower.includes('rating');
  
  // Special styling for flight and restaurant sections
  let cardClassName = 'bg-white border border-gray-200 rounded-xl p-5 space-y-3 shadow-sm hover:shadow-md transition-shadow';
  let titleClassName = 'text-base font-semibold text-gray-900 mb-3';
  
  if (isFlightSection) {
    cardClassName = 'bg-blue-50/60 border-2 border-blue-300/50 rounded-xl p-5 space-y-3 shadow-sm hover:shadow-md transition-shadow';
    titleClassName = 'text-base font-semibold text-blue-900 mb-3 flex items-center gap-2';
  } else if (isRestaurantSection) {
    cardClassName = 'bg-amber-50/60 border-2 border-amber-300/50 rounded-xl p-5 space-y-3 shadow-sm hover:shadow-md transition-shadow';
    titleClassName = 'text-base font-semibold text-amber-900 mb-3 flex items-center gap-2';
  }
  
  return (
    <div className={cardClassName}>
      {hasTitle && (
        <div className={titleClassName}>
          {isFlightSection && <span className="text-lg">✈️</span>}
          {isRestaurantSection && <span className="text-lg">🍽️</span>}
          <span>{section.title}</span>
        </div>
      )}
      <div className="prose prose-sm max-w-none">
        <ReactMarkdown
          components={{
            ul: ({ children }) => (
              <ul className="space-y-2.5 my-4 pl-5 list-disc">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="space-y-2.5 my-4 pl-5 list-decimal">{children}</ol>
            ),
            li: ({ children }) => (
              <li className="text-gray-700 leading-relaxed text-sm">{children}</li>
            ),
            p: ({ children }) => (
              <p className="text-gray-700 mb-3 leading-relaxed text-sm">{children}</p>
            ),
            strong: ({ children }) => (
              <strong className="font-semibold text-gray-900">{children}</strong>
            ),
            h3: ({ children }) => (
              <h3 className="text-sm font-semibold text-gray-800 mt-5 mb-2.5">{children}</h3>
            ),
            h4: ({ children }) => (
              <h4 className="text-xs font-semibold text-gray-700 mt-4 mb-2 uppercase tracking-wide">{children}</h4>
            ),
          }}
        >
          {section.content}
        </ReactMarkdown>
      </div>
    </div>
  );
}

function FollowUpCTA({ question }: { question: string }) {
  // Clean up the question
  let cleanQuestion = question.trim();
  if (!cleanQuestion.endsWith('?') && !cleanQuestion.endsWith('.')) {
    cleanQuestion += '?';
  }
  
  return (
    <div className="mt-6 pt-5 border-t-2 border-dashed border-gray-300">
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-2xl p-5 shadow-md">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center shadow-sm">
            <span className="text-lg">💡</span>
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-900 leading-relaxed">
              {cleanQuestion}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

