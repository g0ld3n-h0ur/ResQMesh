import React from "react";
import { AlertTriangle } from "lucide-react";

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("ResQMesh UI error:", error, info.componentStack);
  }

  private handleReload = () => {
    this.setState({ error: null });
    window.location.reload();
  };

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
          <div className="max-w-md w-full bg-white border border-rose-200 rounded-2xl shadow-sm p-6 space-y-4">
            <div className="flex items-center space-x-3 text-rose-700">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <h1 className="text-sm font-semibold">Something went wrong</h1>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              The portal hit an unexpected error while rendering this view. Check the browser
              console for details, then reload the page.
            </p>
            <pre className="text-[10px] bg-slate-50 border border-slate-200 rounded-lg p-3 overflow-x-auto text-slate-500">
              {this.state.error.message}
            </pre>
            <button
              type="button"
              onClick={this.handleReload}
              className="w-full px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl transition"
            >
              Reload Portal
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
