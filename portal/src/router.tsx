import { createBrowserRouter, Navigate } from "react-router-dom";

import { RequireAuth } from "./auth/RequireAuth";
import { AppLayout } from "./components/AppLayout";
import { LoginPage } from "./routes/login";
import { SignupPage } from "./routes/signup";
import { SitesIndex } from "./routes/sites";
import { SiteLayout } from "./routes/sites/SiteLayout";
import { KnowledgeTab } from "./routes/sites/knowledge";
import { WidgetTab } from "./routes/sites/widget";
import { ConversationsTab } from "./routes/sites/conversations";
import { SettingsTab } from "./routes/sites/settings";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/signup", element: <SignupPage /> },
  {
    path: "/",
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <Navigate to="/sites" replace /> },
      { path: "sites", element: <SitesIndex /> },
      {
        path: "sites/:siteId",
        element: <SiteLayout />,
        children: [
          { index: true, element: <Navigate to="knowledge" replace /> },
          { path: "knowledge", element: <KnowledgeTab /> },
          { path: "widget", element: <WidgetTab /> },
          { path: "conversations", element: <ConversationsTab /> },
          { path: "settings", element: <SettingsTab /> },
        ],
      },
    ],
  },
]);
