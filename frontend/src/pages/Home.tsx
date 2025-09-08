import { Link } from "wouter";
import { ArrowRight, FileText, Search } from "lucide-react";

const Home = () => {
  return (
    <div className="text-center">
      <h1 className="text-4xl font-bold mb-4">歡迎使用智能分析平台</h1>
      <p className="text-lg text-gray-600 dark:text-gray-300 mb-12">請選擇您需要的功能</p>
      <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
        <FeatureCard
          title="找替代料"
          description="上傳單一 Excel 檔案，即時分析並尋找可能的替代料選項。"
          link="/alt"
          icon={<Search className="w-12 h-12 text-blue-500 mb-4" />}
        />
        <FeatureCard
          title="找值"
          description="上傳多個 Excel 與 PDF 檔案，系統將整合資訊並打包結果供您下載。"
          link="/value"
          icon={<FileText className="w-12 h-12 text-green-500 mb-4" />}
        />
      </div>
    </div>
  );
};

interface FeatureCardProps {
  title: string;
  description: string;
  link: string;
  icon: React.ReactNode;
}

const FeatureCard = ({ title, description, link, icon }: FeatureCardProps) => (
  <Link href={link}>
    <a className="block p-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg hover:shadow-xl transition-shadow transform hover:-translate-y-1">
      <div className="flex flex-col items-center">
        {icon}
        <h2 className="text-2xl font-bold mb-3">{title}</h2>
        <p className="text-gray-600 dark:text-gray-400 mb-4">{description}</p>
        <div className="flex items-center justify-center text-blue-500 font-semibold">
          開始使用 <ArrowRight className="ml-2 w-5 h-5" />
        </div>
      </div>
    </a>
  </Link>
);

export default Home;
