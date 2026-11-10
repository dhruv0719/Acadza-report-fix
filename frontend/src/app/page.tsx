export default function HomePage() {
  return (
    <main className="max-w-4xl mx-auto px-4 py-12">
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Acadza AI Report-to-Fix System</h1>
        <p className="text-slate-600 mb-6">
          Phase 1 Foundation: Project initialized with Python/FastAPI backend, data normalization schemas, and Next.js frontend scaffolding.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          <div className="p-4 bg-slate-50 rounded border border-slate-100">
            <div className="text-3xl font-bold text-blue-600">43</div>
            <div className="text-sm text-slate-500">Total Questions</div>
          </div>
          <div className="p-4 bg-slate-50 rounded border border-slate-100">
            <div className="text-3xl font-bold text-blue-600">44</div>
            <div className="text-sm text-slate-500">Student Reports</div>
          </div>
          <div className="p-4 bg-slate-50 rounded border border-slate-100">
            <div className="text-3xl font-bold text-blue-600">18</div>
            <div className="text-sm text-slate-500">Taxonomy Repairs</div>
          </div>
        </div>
      </div>
    </main>
  );
}

