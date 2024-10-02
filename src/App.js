import Content from "./Componets/Content";
import { Header } from "./Componets/Header";
import Navigation from "./Componets/Navigation";

function App() {
  return (
    <div className="flex flex-row gap-x-2">
      <Navigation />
      <Content />
    </div>
  );
}

export default App;
