import FAQEditor from './FAQEditor';

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <FAQEditor treeWorkflowId={id} />;
}
