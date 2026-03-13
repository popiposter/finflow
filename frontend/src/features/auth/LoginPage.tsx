import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { useLoginMutation } from "@/features/auth/session";
import { useAppIntl } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/Button";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const intl = useAppIntl();
  const navigate = useNavigate();
  const location = useLocation();
  const loginMutation = useLoginMutation();
  const { register, handleSubmit, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    await loginMutation.mutateAsync(values);
    const next = (location.state as { from?: string } | null)?.from ?? "/";
    navigate(next, { replace: true });
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
        {formState.errors.email ? (
          <small className="field-error">{formState.errors.email.message}</small>
        ) : null}
      </label>

      <label className="field">
        <span>{intl.formatMessage({ id: "auth.password" })}</span>
        <input type="password" autoComplete="current-password" {...register("password")} />
        {formState.errors.password ? (
          <small className="field-error">{formState.errors.password.message}</small>
        ) : null}
      </label>

      {loginMutation.error ? (
        <div className="callout callout--danger">{loginMutation.error.message}</div>
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
