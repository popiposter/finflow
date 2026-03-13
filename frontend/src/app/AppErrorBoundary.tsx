import type { ReactNode } from "react";
import { Component } from "react";

import { useAppIntl } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/Button";

type ErrorBoundaryProps = {
  children: ReactNode;
  title: string;
  copy: string;
  retryLabel: string;
  homeLabel: string;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

class ErrorBoundaryInner extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    console.error("Unhandled React render error", error);
  }

  private handleRetry = () => {
    this.setState({ hasError: false });
  };

  private handleGoHome = () => {
    window.location.assign("/");
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="app-error-shell">
          <div className="app-error-card">
            <h1 className="section-title">{this.props.title}</h1>
            <p className="muted-copy">{this.props.copy}</p>
            <div className="action-group">
              <Button type="button" onClick={this.handleRetry}>
                {this.props.retryLabel}
              </Button>
              <Button type="button" variant="secondary" onClick={this.handleGoHome}>
                {this.props.homeLabel}
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export function AppErrorBoundary({ children }: { children: ReactNode }) {
  const intl = useAppIntl();

  return (
    <ErrorBoundaryInner
      copy={intl.formatMessage({ id: "errors.boundaryCopy" })}
      homeLabel={intl.formatMessage({ id: "errors.boundaryHome" })}
      retryLabel={intl.formatMessage({ id: "errors.boundaryRetry" })}
      title={intl.formatMessage({ id: "errors.boundaryTitle" })}
    >
      {children}
    </ErrorBoundaryInner>
  );
}

