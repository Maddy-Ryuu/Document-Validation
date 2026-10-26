import React, { useState } from "react";
import { Sidebar, NavItemKey } from "./components/Sidebar";
import { Header } from "./components/Header";
import { Overview } from "./pages/Overview";
import { ApplicationsPage } from "./pages/ApplicationsPage";
import { InstitutionsPage } from "./pages/InstitutionsPage";
import { ApplicationDetailPage } from "./pages/ApplicationDetailPage";
import { ComplianceRulesPage } from "./pages/ComplianceRulesPage";
import { ComingSoonModule } from "./pages/ComingSoonModule";
import { NewApplicationModal } from "./components/NewApplicationModal";
import { NewInstitutionModal } from "./components/NewInstitutionModal";

export function App() {
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
          <ComingSoonModule
            title="Document Review & OCR Engine"
            description="Deep multi-page OCR, PDF authenticity analysis, metadata extraction, and forensic document verification"
            phase="Phase 2"
            highlights={[
              "AICTE Trust Deed & Land Registration Extraction",
              "Fire Safety NOC Digital Signature Inspection",
              "Architect Built-Up Area Plan Sanction Matching",
              "Cryptographic SHA-256 Hash Tampering Audit",
            ]}
          />
        );

      case "rules":
        return <ComplianceRulesPage />;

      case "verification":
        return (
          <ComingSoonModule
            title="Verification Center"
            description="External official registry cross-verification with State Revenue, Fire, and AICTE National Master"
            phase="Phase 3"
            highlights={[
              "State Land Revenue Portal Handshake",
              "Municipal Corporation Sanction Cross-Check",
              "Aadhaar-based Faculty Deposition Verification",
              "UGC & Affiliating University NOC Validation",
            ]}
          />
        );

      case "queue":
        return (
          <ComingSoonModule
            title="Review Queue & Scrutiny Committee"
            description="Worklist allocation, role-based scrutiny officer workflows, and formal objection issuance"
            phase="Phase 2"
            highlights={[
              "Automated Workload & Regional Cell Assignment",
              "Multi-tier Scrutiny Officer Consensus",
              "Formal AICTE Deficiency Letter Generation",
              "Institutional Appeal & Re-scrutiny Workflow",
            ]}
          />
        );

      case "audit":
        return (
          <ComingSoonModule
            title="Audit Trail & Regulatory Log"
            description="Immutable timeline of all inspection actions, rule evaluation history, and reviewer notes"
            phase="Phase 3"
            highlights={[
              "User Action & Decision Fingerprinting",
              "Timestamped Forensic Change History",
              "Exportable Regulatory Compliance Dossier",
              "CBI / Vigilance Inspection Readiness Export",
            ]}
          />
        );

      case "reports":
        return (
          <ComingSoonModule
            title="Regulatory Reports & Analytics"
            description="State-wise sanction compliance metrics, discrepancy breakdown, and annual intake summaries"
            phase="Phase 3"
            highlights={[
              "State & Regional Deficit Heatmaps",
              "Annual Intake & Seat Matrix Trends",
              "Non-Compliance Categorization Reports",
              "Executive AICTE Council Briefing Exporters",
            ]}
          />
        );

      case "settings":
        return (
          <ComingSoonModule
            title="Platform Settings & Access Control"
            description="Role-based permissions, regional bureau configurations, and API keys"
            phase="Phase 3"
            highlights={[
              "RBAC Role Definition (Scrutiny Officer, Council, Admin)",
              "Approval Process Handbook Edition Toggle",
              "Session Timeout & Two-Factor Authentication",
              "Database Backup & Archival Rules",
            ]}
          />
        );

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
      default:
        return currentTab.charAt(0).toUpperCase() + currentTab.slice(1);
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
      default:
        return "Regulatory Administration Module";
    }
  };

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
        <Header title={getHeaderTitle()} subtitle={getHeaderSubtitle()} />

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
