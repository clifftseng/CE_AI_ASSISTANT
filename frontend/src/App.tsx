import { Link, Route, Switch } from "wouter";
import Home from "./pages/Home";
import AltPage from "./pages/AltPage";
import ValuePage from "./pages/ValuePage";

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white dark:bg-gray-800 shadow-md">
        <nav className="container mx-auto px-6 py-3 flex items-center justify-between">
          <Link href="/">
            <a className="text-xl font-bold text-gray-800 dark:text-white">
              智能分析平台
            </a>
          </Link>
          <div className="space-x-4">
            <Link href="/alt">
              <a className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">找替代料</a>
            </Link>
            <Link href="/value">
              <a className="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400">找值</a>
            </Link>
          </div>
        </nav>
      </header>
      <main className="flex-grow container mx-auto p-6">
        <Switch>
          <Route path="/" component={Home} />
          <Route path="/alt" component={AltPage} />
          <Route path="/value" component={ValuePage} />
          <Route>
            <div className="text-center text-2xl font-bold text-gray-700 dark:text-gray-300">
              404: 頁面不存在
            </div>
          </Route>
        </Switch>
      </main>
      <footer className="text-center text-sm text-gray-500 py-4">
        © 2025 全端AI助理
      </footer>
    </div>
  );
}

export default App;
