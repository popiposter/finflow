import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { useRegisterMutation } from "@/features/auth/session";
import { useAppIntl } from "@/shared/lib/i18n";
import { Button } from "@/shared/ui/Button";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const intl = useAppIntl();
  const navigate = useNavigate();
  const registerMutation = useRegisterMutation();
  const { register, handleSubmit, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    await registerMutation.mutateAsync(values);
    navigate("/", { replace: true });
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
        {formState.errors.email ? (
          <small className="field-error">{formState.errors.email.message}</small>
        ) : null}
      </label>

      <label className="field">
        <span>{intl.formatMessage({ id: "auth.password" })}</span>
        <input type="password" autoComplete="new-password" {...register("password")} />
        {formState.errors.password ? (
          <small className="field-error">{formState.errors.password.message}</small>
        ) : null}
      </label>

      {registerMutation.error ? (
        <div className="callout callout--danger">{registerMutation.error.message}</div>
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
