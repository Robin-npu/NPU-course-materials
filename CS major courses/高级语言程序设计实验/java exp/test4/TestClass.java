class Book {

    private String title;
    private int pdate;
    private int words;

    public Book(String title, int pdate, int words) {
        this.title = title;
        this.pdate = pdate;
        this.words = words;
    }

    public double price() {
        double coefficient;
        if (pdate >= 1 && pdate <= 6) {
            coefficient = 1.2;
        } else {
            coefficient = 1.18;
        }
        return (words / 1000.0) * 35 * coefficient;
    }


    public String getTitle() {
        return title;
    }

    public int getPdate() {
        return pdate;
    }

    public int getWords() {
        return words;
    }
}

public class TestClass {
    public static void main(String[] args) {
        Book book = new Book("Java编程思想", 5, 250000);
        System.out.println("Title:" + book.getTitle());
        System.out.println("Pdate:" + book.getPdate());
        System.out.println("Words:" + book.getWords());
        System.out.printf("Price:%.2frmb\n", book.price());
    }
}