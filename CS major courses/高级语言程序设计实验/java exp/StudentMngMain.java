import java.io.*;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

// 学生类，实现Serializable以支持对象序列化
class Student implements Serializable {
    private static final long serialVersionUID = 1L; // 序列化版本号

    private String studentId;   // 学号
    private String name;        // 姓名
    private Date birthDate;     // 出生日期
    private String gender;      // 性别
    private String className;   // 班级

    public Student(String studentId, String name, Date birthDate, String gender, String className) {
        this.studentId = studentId;
        this.name = name;
        this.birthDate = birthDate;
        this.gender = gender;
        this.className = className;
    }

    // Getter 和 Setter 方法
    public String getStudentId() { return studentId; }
    public void setStudentId(String studentId) { this.studentId = studentId; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Date getBirthDate() { return birthDate; }
    public void setBirthDate(Date birthDate) { this.birthDate = birthDate; }
    public String getGender() { return gender; }
    public void setGender(String gender) { this.gender = gender; }
    public String getClassName() { return className; }
    public void setClassName(String className) { this.className = className; }

    @Override
    public String toString() {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        return String.format("学号: %-10s 姓名: %-8s 性别: %-4s 出生日期: %-10s 班级: %-10s",
                studentId, name, gender, sdf.format(birthDate), className);
    }
}

// 学生管理类，负责增删查改及持久化
class StudentManager {
    private Map<String, Student> studentMap; // 使用HashMap存储学生，学号为键
    private static final String DATA_FILE = "students.dat"; // 默认数据文件

    public StudentManager() {
        studentMap = new LinkedHashMap<>(); // 保持插入顺序
    }

    // 1. 添加学生信息
    public boolean addStudent(Student student) {
        if (studentMap.containsKey(student.getStudentId())) {
            System.out.println("错误：学号 " + student.getStudentId() + " 已存在，添加失败。");
            return false;
        }
        studentMap.put(student.getStudentId(), student);
        System.out.println("学生 " + student.getName() + " 添加成功。");
        return true;
    }

    // 2. 根据学号查询学生信息
    public Student queryStudent(String studentId) {
        Student student = studentMap.get(studentId);
        if (student == null) {
            System.out.println("未找到学号为 " + studentId + " 的学生。");
        }
        return student;
    }

    // 3. 根据学号删除学生信息
    public boolean deleteStudent(String studentId) {
        if (studentMap.remove(studentId) != null) {
            System.out.println("学号 " + studentId + " 的学生已删除。");
            return true;
        } else {
            System.out.println("错误：学号 " + studentId + " 不存在，删除失败。");
            return false;
        }
    }

    // 4. 列出所有学生信息
    public void listAllStudents() {
        if (studentMap.isEmpty()) {
            System.out.println("系统中暂无学生信息。");
            return;
        }
        System.out.println("\n========== 学生信息列表 ==========");
        for (Student student : studentMap.values()) {
            System.out.println(student);
        }
        System.out.println("共 " + studentMap.size() + " 名学生。\n");
    }

    // 5. 保存数据到文件（序列化）
    public void saveToFile() {
        try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(DATA_FILE))) {
            oos.writeObject(new ArrayList<>(studentMap.values())); // 保存学生列表
            System.out.println("学生信息已保存到文件 " + DATA_FILE);
        } catch (IOException e) {
            System.err.println("保存文件时出错：" + e.getMessage());
        }
    }

    // 6. 从文件加载数据（反序列化）
    @SuppressWarnings("unchecked")
    public void loadFromFile() {
        File file = new File(DATA_FILE);
        if (!file.exists()) {
            System.out.println("数据文件不存在，将使用空集合启动。");
            return;
        }
        try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream(DATA_FILE))) {
            List<Student> list = (List<Student>) ois.readObject();
            studentMap.clear();
            for (Student s : list) {
                studentMap.put(s.getStudentId(), s);
            }
            System.out.println("已从文件 " + DATA_FILE + " 加载 " + studentMap.size() + " 条学生记录。");
        } catch (IOException | ClassNotFoundException e) {
            System.err.println("加载文件时出错：" + e.getMessage());
        }
    }
}

// 主类，命令行交互
public class StudentMngMain {
    private static Scanner scanner = new Scanner(System.in);
    private static StudentManager manager = new StudentManager();

    public static void main(String[] args) {
        // 启动时加载已有数据
        manager.loadFromFile();

        while (true) {
            printMenu();
            String choice = scanner.nextLine().trim();
            switch (choice) {
                case "1":
                    addStudent();
                    break;
                case "2":
                    queryStudent();
                    break;
                case "3":
                    deleteStudent();
                    break;
                case "4":
                    manager.listAllStudents();
                    break;
                case "5":
                    manager.saveToFile();
                    break;
                case "6":
                    manager.loadFromFile();
                    break;
                case "0":
                    System.out.println("系统退出。");
                    manager.saveToFile(); // 退出时自动保存
                    scanner.close();
                    System.exit(0);
                    break;
                default:
                    System.out.println("无效选项，请重新输入。");
            }
        }
    }

    // 打印菜单
    private static void printMenu() {
        System.out.println("\n========== 学生信息管理系统 ==========");
        System.out.println("1. 添加学生");
        System.out.println("2. 按学号查询学生");
        System.out.println("3. 按学号删除学生");
        System.out.println("4. 显示所有学生");
        System.out.println("5. 保存数据到文件");
        System.out.println("6. 从文件加载数据");
        System.out.println("0. 退出系统");
        System.out.print("请输入选项：");
    }

    // 添加学生时的输入验证和交互
    private static void addStudent() {
        try {
            System.out.print("请输入学号：");
            String id = scanner.nextLine().trim();
            if (id.isEmpty()) {
                System.out.println("学号不能为空！");
                return;
            }

            System.out.print("请输入姓名：");
            String name = scanner.nextLine().trim();
            if (name.isEmpty()) {
                System.out.println("姓名不能为空！");
                return;
            }

            System.out.print("请输入出生日期（格式 yyyy-MM-dd）：");
            String dateStr = scanner.nextLine().trim();
            Date birthDate = parseDate(dateStr);

            System.out.print("请输入性别（男/女）：");
            String gender = scanner.nextLine().trim();
            if (!gender.equals("男") && !gender.equals("女")) {
                System.out.println("性别只能为 '男' 或 '女'！");
                return;
            }

            System.out.print("请输入班级：");
            String className = scanner.nextLine().trim();
            if (className.isEmpty()) {
                System.out.println("班级不能为空！");
                return;
            }

            Student student = new Student(id, name, birthDate, gender, className);
            manager.addStudent(student);
        } catch (ParseException e) {
            System.out.println("日期格式错误，请使用 yyyy-MM-dd 格式。");
        } catch (Exception e) {
            System.out.println("输入错误：" + e.getMessage());
        }
    }

    // 查询学生
    private static void queryStudent() {
        System.out.print("请输入要查询的学号：");
        String id = scanner.nextLine().trim();
        Student student = manager.queryStudent(id);
        if (student != null) {
            System.out.println("查询结果：" + student);
        }
    }

    // 删除学生
    private static void deleteStudent() {
        System.out.print("请输入要删除的学号：");
        String id = scanner.nextLine().trim();
        manager.deleteStudent(id);
    }

    // 解析日期，格式要求 yyyy-MM-dd
    private static Date parseDate(String dateStr) throws ParseException {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        sdf.setLenient(false); // 严格校验日期合法性
        return sdf.parse(dateStr);
    }
}


