import { useMsal } from "@azure/msal-react";
import { Auth } from "aws-amplify";
import { useEffect } from "react";
import { toast } from "react-hot-toast";
import { useAuth } from "react-oidc-context";
import {
  AUTH_WITH_AZUREAD,
  AUTH_WITH_COGNITO,
  AUTH_WITH_OIDC,
  AUTH_WITH_SSO,
} from "../utils/constants";

const useUnauthorized = () => {
  const auth = useAuth();
  const { instance } = useMsal();

  useEffect(() => {
    window.addEventListener("unauthorized", handleUnauthorized);
    return () => window.removeEventListener("unauthorized", handleUnauthorized);
    function handleUnauthorized() {
      console.warn("Not authorized! Logging out");
      toast.error("Please login first!");
      // Object.values(LOCAL_STORAGE_KEYS).forEach((key) =>
      //   localStorage.removeItem(key)
      // );
      if (AUTH_WITH_COGNITO || AUTH_WITH_SSO) {
        Auth.signOut();
      }
      if (AUTH_WITH_OIDC) {
        auth.signoutSilent();
      }
      if (AUTH_WITH_AZUREAD) {
        // instance.logoutRedirect({
        //   postLogoutRedirectUri: "/",
        // });
      }
    }
  }, [auth, instance]);
};

export default useUnauthorized;
