import java.lang.reflect.*;import java.security.MessageDigest;
public class PackageSignProbe {
 public static void main(String[] paths)throws Exception {
  Class<?> c=Class.forName("android.util.apk.ApkSignatureVerifier");
  for(String p:paths)for(String method:new String[]{"verify","unsafeGetCertsWithoutVerification"}) {
   System.out.println("PATH="+p+" MODE="+method);
   try {
    Object details=c.getDeclaredMethod(method,String.class,int.class).invoke(null,p,1);
    Object[] signatures=(Object[])details.getClass().getField("signatures").get(details);
    for(Object signature:signatures) {
     byte[] cert=(byte[])signature.getClass().getMethod("toByteArray").invoke(signature);
     byte[] digest=MessageDigest.getInstance("SHA-256").digest(cert);StringBuilder out=new StringBuilder();
     for(byte b:digest)out.append(String.format("%02x",b&255));System.out.println("CERT="+out);
    }
   } catch(Exception e) { Throwable cause=e instanceof InvocationTargetException?e.getCause():e;System.out.println("FAILED="+cause); }
  }
 }
}
