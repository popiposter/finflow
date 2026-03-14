import { useForm } from "react-hook-form";
import { useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { useLoginMutation } from "@/features/auth/session";
import { applyApiFieldErrors } from "@/shared/lib/api-errors";
import { useAppIntl } from "@/shared/lib/i18n";
import { getFieldErrorMessage, getValidationMessages } from "@/shared/lib/validation";
import { ApiErrorCallout } from "@/shared/ui/ApiErrorCallout";
import { Button } from "@/shared/ui/Button";

type FormValues = {
  email: string;
  password: string;
};

export function LoginPage() {
  const intl = useAppIntl();
  const navigate = useNavigate();
  const location = useLocation();
  const loginMutation = useLoginMutation();
  const validation = getValidationMessages(intl);
  const schema = useMemo(
    () =>
      z.object({
        email: z.string().trim().min(1, validation.required).email(validation.invalidEmail),
        password: z.string().min(8, validation.passwordMin),
      }),
    [validation],
  );
  const { register, handleSubmit, formState, setError } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await loginMutation.mutateAsync(values);
      toast.success(intl.formatMessage({ id: "toast.loggedIn" }));
      const next = (location.state as { from?: string } | null)?.from ?? "/";
      navigate(next, { replace: true });
    } catch (error) {
      applyApiFieldErrors(error, setError, intl);
    }
  });

  return (
    <form className="form-stack" onSubmit={onSubmit}>
      <div>
        <h2 className="section-title">{intl.formatMessage({ id: "auth.loginTitle" })}</h2>
        <p className="muted-copy">{intl.formatMessage({ id: "auth.loginCopy" })}</p>
      </div>

      <label className="field">
        <span>{intl.formatMessage({ id: "auth.email" })}</span>
        <input type="email" autoComplete="email" {...register("email")} />
        {getFieldErrorMessage(formState.errors.email) ? (
          <small className="field-error">{getFieldErrorMessage(formState.errors.email)}</small>
        ) : null}
      </label>

      <label className="field">
        <span>{intl.formatMessage({ id: "auth.password" })}</span>
        <input type="password" autoComplete="current-password" {...register("password")} />
        {getFieldErrorMessage(formState.errors.password) ? (
          <small className="field-error">{getFieldErrorMessage(formState.errors.password)}</small>
        ) : null}
      </label>

      {loginMutation.error ? (
        <ApiErrorCallout error={loginMutation.error} />
      ) : null}

      <Button disabled={loginMutation.isPending} type="submit">
        {loginMutation.isPending
          ? intl.formatMessage({ id: "auth.signingIn" })
          : intl.formatMessage({ id: "auth.signIn" })}
      </Button>

      <p className="muted-copy">
        {intl.formatMessage({ id: "auth.newHere" })}{" "}
        <Link to="/register">{intl.formatMessage({ id: "auth.createAccountLink" })}</Link>
      </p>
    </form>
  );
}
