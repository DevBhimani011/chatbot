
import { ApolloWrapper } from '@/lib/apollo-wrapper';

export default function WorkflowLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ApolloWrapper>{children}</ApolloWrapper>;
}
