export default function AnalysisLoader() {
  return (
    <div className="flex items-center gap-2 text-blue-600 text-sm py-2 px-4 bg-blue-50 rounded border border-blue-200">
      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
      <span>Analyzing tool execution with LLM...</span>
    </div>
  );
}

