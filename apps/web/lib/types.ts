export type SmtpProvider = {
  id: number;
  name: string;
  host: string;
  port: number;
  username: string | null;
  use_tls: boolean;
  created_at: string;
};

export type SmtpProviderCreate = {
  name: string;
  host: string;
  port: number;
  username?: string;
  password?: string;
  use_tls: boolean;
};
