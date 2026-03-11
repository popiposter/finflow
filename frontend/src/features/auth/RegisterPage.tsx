import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { useRegisterMutation } from "@/features/auth/session";
import { Button } from "@/shared/ui/Button";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
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
        <h2 className="section-title">Create your workspace</h2>
        <p className="muted-copy">
          Start with secure cookie-based auth and install the app once you're in.
        </p>
      </div>

      <label className="field">
        <span>Email</span>
        <input type="email" autoComplete="email" {...register("email")} />
        {formState.errors.email ? (
          <small className="field-error">{formState.errors.email.message}</small>
        ) : null}
      </label>

      <label className="field">
        <span>Password</span>
        <input type="password" autoComplete="new-password" {...register("password")} />
        {formState.errors.password ? (
          <small className="field-error">{formState.errors.password.message}</small>
        ) : null}
      </label>

      {registerMutation.error ? (
        <div className="callout callout--danger">{registerMutation.error.message}</div>
      ) : null}

      <Button disabled={registerMutation.isPending} type="submit">
        {registerMutation.isPending ? "Creating..." : "Create account"}
      </Button>

      <p className="muted-copy">
        Already have access? <Link to="/login">Sign in</Link>
      </p>
    </form>
  );
}
