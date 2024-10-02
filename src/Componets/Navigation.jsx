const Navigation = () => {
  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex justify-between items-center flex-col">
        <div className="text-xl font-bold">AI Conversations</div>
        <div className="space-x-4">
          <div className="hover:text-gray-300">Conversations</div>
          <div className="hover:text-gray-300">Groups</div>
        </div>
      </div>
    </nav>
  );
};
export default Navigation;
