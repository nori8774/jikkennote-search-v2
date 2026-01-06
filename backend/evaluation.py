"""
RAG性能評価モジュール

機能:
- nDCG@K (Normalized Discounted Cumulative Gain)
- Precision@K
- Recall@K
- MRR (Mean Reciprocal Rank)
- テストケース管理
- バッチ評価
"""

import os
import json
import csv
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import math
import pandas as pd
from io import StringIO

from config import config


@dataclass
class TestCase:
    """評価用テストケース"""
    id: str
    name: str
    query: Dict[str, str]  # {"purpose": "...", "materials": "...", "methods": "..."}
    ground_truth: List[Dict]  # [{"note_id": "...", "relevance": 5}, ...]
    created_at: Optional[str] = None


@dataclass
class EvaluationMetrics:
    """評価指標"""
    ndcg_10: float
    precision_3: float
    precision_5: float
    precision_10: float
    recall_10: float
    mrr: float


@dataclass
class EvaluationResult:
    """評価結果"""
    test_case_id: str
    metrics: EvaluationMetrics
    ranking: List[Dict]  # [{"note_id": "...", "rank": 1, "score": 0.9, "relevance": 5}, ...]
    comparison: List[Dict]  # [{"note_id": "...", "expected_rank": 1, "actual_rank": 2, "relevance": 5}, ...]


class Evaluator:
    """RAG評価クラス"""

    def __init__(self, test_cases_file: Optional[str] = None):
        """
        Args:
            test_cases_file: テストケースを保存するJSONファイル
        """
        self.test_cases_file = test_cases_file or os.path.join(config.Config.CHROMA_DB_FOLDER, 'test_cases.json')
        self.test_cases: List[TestCase] = []
        self.load_test_cases()

    def load_test_cases(self):
        """テストケースを読み込み"""
        if not os.path.exists(self.test_cases_file):
            self.test_cases = []
            return

        try:
            with open(self.test_cases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.test_cases = [
                TestCase(
                    id=tc['id'],
                    name=tc['name'],
                    query=tc['query'],
                    ground_truth=tc['ground_truth'],
                    created_at=tc.get('created_at')
                )
                for tc in data
            ]
            print(f"テストケースを読み込みました: {len(self.test_cases)}件")
        except Exception as e:
            print(f"テストケースの読み込みに失敗: {e}")
            self.test_cases = []

    def save_test_cases(self):
        """テストケースを保存"""
        try:
            # フォルダが存在しない場合は作成
            os.makedirs(os.path.dirname(self.test_cases_file), exist_ok=True)

            data = [asdict(tc) for tc in self.test_cases]
            with open(self.test_cases_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"テストケースを保存しました: {len(self.test_cases)}件")
            return True
        except Exception as e:
            print(f"テストケースの保存に失敗: {e}")
            return False

    def add_test_case(self, test_case: TestCase) -> bool:
        """テストケースを追加"""
        # 既存チェック
        if any(tc.id == test_case.id for tc in self.test_cases):
            print(f"テストケースが既に存在します: {test_case.id}")
            return False

        if not test_case.created_at:
            test_case.created_at = datetime.now().isoformat()

        self.test_cases.append(test_case)
        return self.save_test_cases()

    def get_test_case(self, test_case_id: str) -> Optional[TestCase]:
        """テストケースを取得"""
        for tc in self.test_cases:
            if tc.id == test_case_id:
                return tc
        return None

    def get_all_test_cases(self) -> List[Dict]:
        """全テストケースを取得"""
        return [asdict(tc) for tc in self.test_cases]

    def delete_test_case(self, test_case_id: str) -> bool:
        """テストケースを削除"""
        original_len = len(self.test_cases)
        self.test_cases = [tc for tc in self.test_cases if tc.id != test_case_id]

        if len(self.test_cases) < original_len:
            return self.save_test_cases()
        return False

    def import_from_csv(self, csv_content: str) -> int:
        """
        CSVからテストケースをインポート

        CSVフォーマット:
        test_case_id, test_case_name, purpose, materials, methods, note_id, rank, relevance
        TC001, "テストケース1", "目的", "材料", "方法", "ID3-14", 1, 5
        TC001, "テストケース1", "目的", "材料", "方法", "ID3-15", 2, 4
        ...

        Returns:
            インポートしたテストケース数
        """
        try:
            reader = csv.DictReader(StringIO(csv_content))

            # テストケースIDごとにグループ化
            cases_dict = {}
            for row in reader:
                tc_id = row.get('test_case_id', '').strip()
                if not tc_id:
                    continue

                if tc_id not in cases_dict:
                    cases_dict[tc_id] = {
                        'id': tc_id,
                        'name': row.get('test_case_name', tc_id),
                        'query': {
                            'purpose': row.get('purpose', ''),
                            'materials': row.get('materials', ''),
                            'methods': row.get('methods', '')
                        },
                        'ground_truth': []
                    }

                note_id = row.get('note_id', '').strip()
                if note_id:
                    cases_dict[tc_id]['ground_truth'].append({
                        'note_id': note_id,
                        'rank': int(row.get('rank', 0)),
                        'relevance': int(row.get('relevance', 1))
                    })

            # テストケースを追加
            count = 0
            for tc_data in cases_dict.values():
                test_case = TestCase(
                    id=tc_data['id'],
                    name=tc_data['name'],
                    query=tc_data['query'],
                    ground_truth=tc_data['ground_truth'],
                    created_at=datetime.now().isoformat()
                )
                if self.add_test_case(test_case):
                    count += 1

            return count

        except Exception as e:
            print(f"CSVインポートに失敗: {e}")
            return 0

    def import_from_excel(self, file_path: str) -> int:
        """
        Excelからテストケースをインポート

        Returns:
            インポートしたテストケース数
        """
        try:
            df = pd.read_excel(file_path)

            # DataFrameをCSV形式に変換してimport_from_csvを利用
            csv_content = df.to_csv(index=False)
            return self.import_from_csv(csv_content)

        except Exception as e:
            print(f"Excelインポートに失敗: {e}")
            return 0

    @staticmethod
    def calculate_dcg(relevances: List[float], k: Optional[int] = None) -> float:
        """
        DCG (Discounted Cumulative Gain) を計算

        Args:
            relevances: 関連度のリスト（ランキング順）
            k: 上位K件まで計算（Noneの場合は全て）

        Returns:
            DCGスコア
        """
        if k is not None:
            relevances = relevances[:k]

        dcg = 0.0
        for i, rel in enumerate(relevances, start=1):
            dcg += rel / math.log2(i + 1)

        return dcg

    @staticmethod
    def calculate_ndcg(relevances: List[float], k: int = 10) -> float:
        """
        nDCG (Normalized DCG) を計算

        Args:
            relevances: 実際のランキングの関連度リスト
            k: 上位K件まで計算

        Returns:
            nDCGスコア (0.0-1.0)
        """
        dcg = Evaluator.calculate_dcg(relevances, k)

        # 理想的なランキング（関連度の降順）
        ideal_relevances = sorted(relevances, reverse=True)
        idcg = Evaluator.calculate_dcg(ideal_relevances, k)

        if idcg == 0:
            return 0.0

        return dcg / idcg

    @staticmethod
    def calculate_precision_at_k(relevant_count: int, k: int) -> float:
        """
        Precision@K を計算

        Args:
            relevant_count: 上位K件中の関連文書数
            k: K

        Returns:
            Precision@K (0.0-1.0)
        """
        if k == 0:
            return 0.0
        return relevant_count / k

    @staticmethod
    def calculate_recall_at_k(relevant_count: int, total_relevant: int, k: int) -> float:
        """
        Recall@K を計算

        Args:
            relevant_count: 上位K件中の関連文書数
            total_relevant: 全体の関連文書数
            k: K

        Returns:
            Recall@K (0.0-1.0)
        """
        if total_relevant == 0:
            return 0.0
        return relevant_count / total_relevant

    @staticmethod
    def calculate_mrr(ranks: List[int]) -> float:
        """
        MRR (Mean Reciprocal Rank) を計算

        Args:
            ranks: 最初の関連文書が出現したランク位置のリスト

        Returns:
            MRRスコア (0.0-1.0)
        """
        if not ranks:
            return 0.0

        reciprocal_ranks = [1.0 / rank for rank in ranks if rank > 0]

        if not reciprocal_ranks:
            return 0.0

        return sum(reciprocal_ranks) / len(ranks)

    def evaluate(self, test_case: TestCase, retrieved_results: List[Dict]) -> EvaluationResult:
        """
        1つのテストケースを評価

        Args:
            test_case: テストケース
            retrieved_results: 検索結果 [{"note_id": "...", "score": 0.9}, ...]

        Returns:
            評価結果
        """
        # 正解ランキングをdictに変換
        ground_truth_dict = {
            gt['note_id']: {'rank': gt.get('rank', i+1), 'relevance': gt.get('relevance', 1)}
            for i, gt in enumerate(test_case.ground_truth)
        }

        # 検索結果のランキングを作成
        ranking = []
        relevances = []

        for i, result in enumerate(retrieved_results[:10], start=1):
            note_id = result['note_id']
            gt = ground_truth_dict.get(note_id, {'relevance': 0})

            ranking.append({
                'note_id': note_id,
                'rank': i,
                'score': result.get('score', 0.0),
                'relevance': gt['relevance']
            })
            relevances.append(gt['relevance'])

        # 評価指標を計算
        ndcg_10 = self.calculate_ndcg(relevances, k=10)

        # Precision@K
        relevant_3 = sum(1 for r in relevances[:3] if r > 0)
        relevant_5 = sum(1 for r in relevances[:5] if r > 0)
        relevant_10 = sum(1 for r in relevances[:10] if r > 0)

        precision_3 = self.calculate_precision_at_k(relevant_3, 3)
        precision_5 = self.calculate_precision_at_k(relevant_5, 5)
        precision_10 = self.calculate_precision_at_k(relevant_10, 10)

        # Recall@10
        total_relevant = len([gt for gt in test_case.ground_truth if gt.get('relevance', 0) > 0])
        recall_10 = self.calculate_recall_at_k(relevant_10, total_relevant, 10)

        # MRR
        first_relevant_rank = next((i+1 for i, r in enumerate(relevances) if r > 0), 0)
        mrr = 1.0 / first_relevant_rank if first_relevant_rank > 0 else 0.0

        metrics = EvaluationMetrics(
            ndcg_10=ndcg_10,
            precision_3=precision_3,
            precision_5=precision_5,
            precision_10=precision_10,
            recall_10=recall_10,
            mrr=mrr
        )

        # 比較データを作成
        comparison = []
        for note_id, gt in ground_truth_dict.items():
            actual_rank = next((r['rank'] for r in ranking if r['note_id'] == note_id), None)
            comparison.append({
                'note_id': note_id,
                'expected_rank': gt['rank'],
                'actual_rank': actual_rank,
                'relevance': gt['relevance']
            })

        return EvaluationResult(
            test_case_id=test_case.id,
            metrics=metrics,
            ranking=ranking,
            comparison=comparison
        )

    def batch_evaluate(self, results: List[Tuple[TestCase, List[Dict]]]) -> Dict:
        """
        バッチ評価

        Args:
            results: [(test_case, retrieved_results), ...]

        Returns:
            集計結果 {"average_metrics": {...}, "individual_results": [...]}
        """
        individual_results = []

        for test_case, retrieved_results in results:
            eval_result = self.evaluate(test_case, retrieved_results)
            individual_results.append({
                'test_case_id': test_case.id,
                'test_case_name': test_case.name,
                'metrics': asdict(eval_result.metrics)
            })

        # 平均を計算
        if individual_results:
            avg_metrics = {}
            metric_keys = list(individual_results[0]['metrics'].keys())

            for key in metric_keys:
                values = [r['metrics'][key] for r in individual_results]
                avg_metrics[key] = sum(values) / len(values)
        else:
            avg_metrics = {}

        return {
            'average_metrics': avg_metrics,
            'individual_results': individual_results
        }


# グローバルインスタンス
_evaluator = None


def get_evaluator() -> Evaluator:
    """評価器のシングルトンインスタンスを取得"""
    global _evaluator
    if _evaluator is None:
        _evaluator = Evaluator()
    return _evaluator
