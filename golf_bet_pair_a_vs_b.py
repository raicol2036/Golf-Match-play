import csv
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Player:
    name: str
    handicap: float = 0.0  # 默认差点为0

@dataclass
class Hole:
    number: int
    par: int
    handicap_rank: int  # 球洞难度排名

@dataclass
class Course:
    name: str
    area: str
    total_par: int
    holes: List[Hole]

class GolfScoreSystem:
    def __init__(self):
        self.players: List[Player] = []
        self.course: Course = None
    
    def load_players(self, filename: str) -> None:
        """从CSV文件加载球员数据（只有姓名）"""
        try:
            with open(filename, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        name = row['name'].strip()
                        if name:  # 确保姓名不为空
                            self.players.append(Player(name))
                    except KeyError as e:
                        print(f"跳过无效的行: {row}. 错误: 缺少姓名字段")
        except FileNotFoundError:
            print(f"错误: 文件 {filename} 未找到")
        except Exception as e:
            print(f"加载球员数据时出错: {e}")
    
    def load_course(self, filename: str) -> None:
        """从CSV文件加载球场数据"""
        holes = []
        try:
            with open(filename, mode='r', newline='', encoding='utf-8') as file:
                # 使用制表符分隔（因为您显示的字段是用制表符分隔的）
                reader = csv.DictReader(file, delimiter='\t')
                course_name = ""
                area = ""
                total_par = 0
                
                for row in reader:
                    try:
                        if not course_name:
                            course_name = row.get('course_name', '未知球场').strip()
                            area = row.get('area', '').strip()
                        
                        hole_num = int(row['hole'])
                        par = int(row['par'])
                        hcp = int(row['hcp'])
                        
                        holes.append(Hole(hole_num, par, hcp))
                        total_par += par
                    except (KeyError, ValueError) as e:
                        print(f"跳过无效的行: {row}. 错误: {e}")
                
                self.course = Course(course_name, area, total_par, holes)
        except FileNotFoundError:
            print(f"错误: 文件 {filename} 未找到")
        except Exception as e:
            print(f"加载球场数据时出错: {e}")
    
    def set_player_handicaps(self, handicaps: Dict[str, float]) -> None:
        """设置每位球员的差点"""
        for player in self.players:
            if player.name in handicaps:
                player.handicap = handicaps[player.name]
    
    def calculate_scores(self, player_scores: Dict[str, List[int]]) -> Dict[str, Dict[str, int]]:
        """
        计算每个球员的比分
        :param player_scores: 字典 {球员姓名: [每洞得分]}
        :return: 字典 {球员姓名: {'gross_score': 总杆数, 'net_score': 净杆数, 'stableford': 史特伯福特积分}}
        """
        results = {}
        
        if not self.course:
            print("错误: 未加载球场数据")
            return results
        
        if not self.players:
            print("警告: 没有加载任何球员")
            return results
        
        for player in self.players:
            if player.name not in player_scores:
                print(f"警告: 没有找到球员 {player.name} 的得分数据")
                continue
            
            scores = player_scores[player.name]
            if len(scores) != len(self.course.holes):
                print(f"警告: 球员 {player.name} 的得分数量({len(scores)})与球洞数量({len(self.course.holes)})不匹配")
                continue
            
            gross_score = sum(scores)
            net_score = gross_score
            
            # 计算净杆数 (总杆数 - 差点)
            if player.handicap > 0:
                handicap_strokes = int(round(player.handicap))
                
                # 分配差点杆数到最难的前N个洞
                sorted_holes = sorted(self.course.holes, key=lambda h: h.handicap_rank)
                net_scores_per_hole = scores.copy()
                
                for hole in sorted_holes[:handicap_strokes]:
                    hole_index = hole.number - 1  # 转换为0-based索引
                    net_scores_per_hole[hole_index] = max(1, net_scores_per_hole[hole_index] - 1)
                
                net_score = sum(net_scores_per_hole)
            
            # 计算史特伯福特积分
            stableford_points = 0
            for i, hole in enumerate(self.course.holes):
                adjusted_score = scores[i]
                
                # 应用差点调整
                if player.handicap > 0:
                    hole_rank = hole.handicap_rank
                    if hole_rank <= player.handicap:
                        adjusted_score -= 1
                
                points = 0
                diff = adjusted_score - (hole.par + 2)  # 双柏忌是标准杆+2
                
                if adjusted_score == 1 and hole.par >= 4:  # 信天翁(除了三杆洞)
                    points = 8
                elif adjusted_score <= hole.par - 3:  # 双鹰或更好
                    points = 5
                elif adjusted_score == hole.par - 2:  # 老鹰
                    points = 4
                elif adjusted_score == hole.par - 1:  # 小鸟
                    points = 3
                elif adjusted_score == hole.par:  # 标准杆
                    points = 2
                elif adjusted_score == hole.par + 1:  # 柏忌
                    points = 1
                # 高于柏忌+1没有积分
                
                stableford_points += max(0, points)
            
            results[player.name] = {
                'gross_score': gross_score,
                'net_score': net_score,
                'stableford': stableford_points,
                'handicap': player.handicap
            }
        
        return results
    
    def display_results(self, results: Dict[str, Dict[str, int]]) -> None:
        """显示比赛结果"""
        if not results:
            print("没有可显示的结果")
            return
        
        print("\n高尔夫比赛结果")
        print("=" * 60)
        print(f"球场: {self.course.name} ({self.course.area})")
        print(f"标准杆: {self.course.total_par}")
        print("-" * 60)
        print("{:<20} {:<10} {:<10} {:<10} {:<10}".format(
            "球员", "总杆数", "净杆数", "差点", "积分"
        ))
        print("-" * 60)
        
        # 按净杆数排序
        sorted_results = sorted(results.items(), key=lambda x: x[1]['net_score'])
        
        for player, data in sorted_results:
            print("{:<20} {:<10} {:<10} {:<10} {:<10}".format(
                player,
                data['gross_score'],
                data['net_score'],
                data['handicap'],
                data['stableford']
            ))
        
        print("=" * 60)


# 示例用法
if __name__ == "__main__":
    # 初始化系统
    golf_system = GolfScoreSystem()
    
    # 加载数据
    golf_system.load_players("players.csv")
    golf_system.load_course("course_db.csv")
    
    # 设置球员差点 (在实际应用中可以从输入或文件获取)
    handicaps = {
        "张三": 12.5,
        "李四": 18.0,
        "王五": 8.2
    }
    golf_system.set_player_handicaps(handicaps)
    
    # 假设的球员得分数据 (在实际应用中可以从输入或文件获取)
    # 格式: {球员姓名: [每洞得分, ...]}
    # 注意: 得分顺序必须与球洞顺序一致
    player_scores = {
        "张三": [4, 5, 3, 4, 4, 5, 3, 4, 4, 5, 4, 4, 3, 5, 4, 4, 3, 5],
        "李四": [5, 6, 4, 5, 5, 6, 4, 5, 5, 6, 5, 5, 4, 6, 5, 5, 4, 6],
        "王五": [4, 4, 3, 4, 3, 4, 3, 4, 3, 4, 4, 3, 3, 4, 4, 3, 3, 4]
    }
    
    # 计算比分
    results = golf_system.calculate_scores(player_scores)
    
    # 显示结果
    golf_system.display_results(results)
