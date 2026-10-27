public class NumTest{
    public static void main (String args[]) {
        int n,num,num1;
        System.out.println("Numbers divisible by 3 and 7 from 1 to 1000 are:");
        for (n=1;n<=1000;n++) {
            num =n%3;
            num1=n%7;
            if (num==0) {
                if (num1==0)
                    System.out.print(n+" ");
            }
        }
        System.out.println(" ");
    }
}
