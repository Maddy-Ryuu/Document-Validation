import React, { useState, useEffect } from "react";
import { LoginPage } from "./pages/LoginPage";
import { AuthUser } from "./types";
import { api } from "./services/api";
import { RotateCw } from "lucide-react";
import { Sidebar, NavItemKey } from "./components/Sidebar";
import { Header } from "./components/Header";
import { Overview } from "./pages/Overview";
import { ApplicationsPage } from "./pages/ApplicationsPage";
import { InstitutionsPage } from "./pages/InstitutionsPage";
import { ApplicationDetailPage } from "./pages/ApplicationDetailPage";
import { ComplianceRulesPage } from "./pages/ComplianceRulesPage";
import { DocumentReviewPage } from "./pages/DocumentReviewPage";
import { VerificationCenterPage } from "./pages/VerificationCenterPage";
import { ReviewQueuePage } from "./pages/ReviewQueuePage";
import { AuditTrailPage } from "./pages/AuditTrailPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { NewApplicationModal } from "./components/NewApplicationModal";
import { NewInstitutionModal } from "./components/NewInstitutionModal";

export function App() {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(() => {
    try {
      const saved = localStorage.getItem("aicte_auth_user");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const user = await api.getCurrentUser();
      setCurrentUser(user);
    } catch {
      setCurrentUser(null);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLoginSuccess = (user: AuthUser) => {
    setCurrentUser(user);
  };

  const handleLogout = async () => {
    await api.logout();
    setCurrentUser(null);
  };

  const [currentTab, setCurrentTab] = useState<NavItemKey>("overview");
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);

  // Modals
  const [isNewAppModalOpen, setIsNewAppModalOpen] = useState(false);
  const [isNewInstModalOpen, setIsNewInstModalOpen] = useState(false);

  // Refresh trigger to reload data dynamically
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const triggerRefresh = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleApplicationCreated = (newApp: any) => {
    triggerRefresh();
    // Navigate to newly created application detail directly
    if (newApp && newApp.id) {
      setSelectedAppId(newApp.id);
      setCurrentTab("applications");
    }
  };

  const handleInstitutionCreated = () => {
    triggerRefresh();
  };

  const renderContent = () => {
    // If an application detail is selected
    if (selectedAppId) {
      return (
        <ApplicationDetailPage
          applicationId={selectedAppId}
          onBack={() => setSelectedAppId(null)}
          onRefresh={triggerRefresh}
        />
      );
    }

    switch (currentTab) {
      case "overview":
        return (
          <Overview
            onOpenNewAppModal={() => setIsNewAppModalOpen(true)}
            onSelectApplication={(id) => setSelectedAppId(id)}
            refreshTrigger={refreshTrigger}
          />
        );

      case "applications":
        return (
          <ApplicationsPage
            onOpenNewAppModal={() => setIsNewAppModalOpen(true)}
            onSelectApplication={(id) => setSelectedAppId(id)}
            refreshTrigger={refreshTrigger}
          />
        );

      case "institutions":
        return (
          <InstitutionsPage
            onOpenNewInstModal={() => setIsNewInstModalOpen(true)}
            refreshTrigger={refreshTrigger}
          />
        );

      case "documents":
        return (
          <DocumentReviewPage
            onSelectApplication={(id) => setSelectedAppId(id)}
            refreshTrigger={refreshTrigger}
          />
        );

      case "rules":
        return <ComplianceRulesPage />;

      case "verification":
        return (
          <VerificationCenterPage
            onSelectApplication={(id) => setSelectedAppId(id)}
            refreshTrigger={refreshTrigger}
          />
        );

      case "queue":
        return (
          <ReviewQueuePage
            onSelectApplication={(id) => setSelectedAppId(id)}
            refreshTrigger={refreshTrigger}
          />
        );

      case "audit":
        return (
          <AuditTrailPage
            onSelectApplication={(id) => setSelectedAppId(id)}
            refreshTrigger={refreshTrigger}
          />
        );

      case "reports":
        return (
          <ReportsPage
            onSelectApplication={(id) => setSelectedAppId(id)}
            refreshTrigger={refreshTrigger}
          />
        );

      case "settings":
        return <SettingsPage />;

      default:
        return null;
    }
  };

  const getHeaderTitle = () => {
    if (selectedAppId) return "Application Scrutiny Dossier";
    switch (currentTab) {
      case "overview":
        return "Application Overview";
      case "applications":
        return "Applications Registry";
      case "institutions":
        return "Institutions Master Registry";
      case "documents":
        return "Document Review & OCR Scrutiny";
      case "rules":
        return "Regulatory Compliance Rules";
      case "verification":
        return "Verification Center";
      case "queue":
        return "Scrutiny Officer Review Queue";
      case "audit":
        return "Regulatory Audit Trail";
      case "reports":
        return "Reports & Analytics";
      case "settings":
        return "Platform Settings & Security Profile";
      default:
        return "AICTE Scrutiny Portal";
    }
  };

  const getHeaderSubtitle = () => {
    if (selectedAppId) return "Detailed Inspection & Evidence Review";
    switch (currentTab) {
      case "overview":
        return "Validation & Compliance Workspace";
      case "applications":
        return "AICTE Formal Submission Tracking";
      case "institutions":
        return "Accredited Technical Institutions";
      case "documents":
        return "Cryptographic Verification & OCR Scrutiny";
      case "rules":
        return "Approval Process Handbook (APH 2026-27)";
      case "verification":
        return "Statutory Evidence Matching & Decision Support";
      case "queue":
        return "Prioritized Application Worklist";
      case "audit":
        return "Immutable Forensic Change History";
      case "reports":
        return "Institutional Compliance Metrics & Exporters";
      case "settings":
        return "Backend Infrastructure & Officer Identity";
      default:
        return "Regulatory Administration Module";
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-surface-muted flex flex-col items-center justify-center space-y-3">
        <RotateCw className="w-8 h-8 animate-spin text-primary-orange" />
        <span className="text-xs text-secondary-text font-medium">Verifying AICTE regulatory credentials...</span>
      </div>
    );
  }

  if (!currentUser) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="flex h-screen bg-white overflow-hidden text-primary-text">
      {/* Persistent Left Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setSelectedAppId(null);
          setCurrentTab(tab);
        }}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col h-screen overflow-y-auto bg-background">
        <Header title={getHeaderTitle()} subtitle={getHeaderSubtitle()} user={currentUser} onLogout={handleLogout} />

        <main className="flex-1 pb-16">{renderContent()}</main>
      </div>

      {/* New Application Modal */}
      <NewApplicationModal
        isOpen={isNewAppModalOpen}
        onClose={() => setIsNewAppModalOpen(false)}
        onSuccess={handleApplicationCreated}
      />

      {/* New Institution Modal */}
      <NewInstitutionModal
        isOpen={isNewInstModalOpen}
        onClose={() => setIsNewInstModalOpen(false)}
        onSuccess={handleInstitutionCreated}
      />
    </div>
  );
}

export default App;
