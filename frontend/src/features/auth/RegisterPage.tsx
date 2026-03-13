import { useForm } from "react-hook-form";
import { useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { useRegisterMutation } from "@/features/auth/session";
import { applyApiFieldErrors } from "@/shared/lib/api-errors";
import { useAppIntl } from "@/shared/lib/i18n";
import { getFieldErrorMessage, getValidationMessages } from "@/shared/lib/validation";
import { ApiErrorCallout } from "@/shared/ui/ApiErrorCallout";
import { Button } from "@/shared/ui/Button";

type FormValues = {
  email: string;
  password: string;
};

export function RegisterPage() {
  const intl = useAppIntl();
  const navigate = useNavigate();
  const registerMutation = useRegisterMutation();
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
      await registerMutation.mutateAsync(values);
      navigate("/", { replace: true });
    } catch (error) {
      applyApiFieldErrors(error, setError, intl);
    }
  });

  return (
    <form className="form-stack" onSubmit={onSubmit}>
      <div>
        <h2 className="section-title">{intl.formatMessage({ id: "auth.registerTitle" })}</h2>
        <p className="muted-copy">{intl.formatMessage({ id: "auth.registerCopy" })}</p>
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
        <input type="password" autoComplete="new-password" {...register("password")} />
        {getFieldErrorMessage(formState.errors.password) ? (
          <small className="field-error">{getFieldErrorMessage(formState.errors.password)}</small>
        ) : null}
      </label>

      {registerMutation.error ? (
        <ApiErrorCallout error={registerMutation.error} />
      ) : null}

      <Button disabled={registerMutation.isPending} type="submit">
        {registerMutation.isPending
          ? intl.formatMessage({ id: "common.creating" })
          : intl.formatMessage({ id: "auth.createAccount" })}
      </Button>

      <p className="muted-copy">
        {intl.formatMessage({ id: "auth.alreadyHaveAccess" })}{" "}
        <Link to="/login">{intl.formatMessage({ id: "auth.signIn" })}</Link>
      </p>
    </form>
  );
}
