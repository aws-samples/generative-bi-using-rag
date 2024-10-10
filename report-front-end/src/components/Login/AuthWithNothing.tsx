import React, { useEffect } from "react";
import App from "../../app";
import { useDispatch } from "react-redux";
import { ActionType } from "../../utils/helpers/types";

const AuthWithNothing: React.FC = () => {
  const dispatch = useDispatch();
  useEffect(() => {
    dispatch({
      type: ActionType.UpdateUserInfo,
      state: {
        userId: "Anonymous",
        displayName: "Anonymous",
        loginExpiration: 0,
        isLogin: true,
        username: "Anonymous",
      },
    });
  }, [dispatch]);

  return <App />;
};

export default AuthWithNothing;
