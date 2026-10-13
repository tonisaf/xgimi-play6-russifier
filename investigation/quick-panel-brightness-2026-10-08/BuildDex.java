import java.io.File;
import java.nio.file.*;
import brut.androlib.src.SmaliBuilder;
import brut.directory.ExtFile;
import com.android.tools.smali.dexlib2.Opcodes;
import com.android.tools.smali.dexlib2.writer.builder.DexBuilder;
import com.android.tools.smali.dexlib2.writer.io.FileDataStore;
public class BuildDex {
  public static void main(String[] args) throws Exception {
    Path root=Path.of(args[0]);
    DexBuilder dex=new DexBuilder(new Opcodes(30,-1));
    SmaliBuilder builder=new SmaliBuilder(new ExtFile(args[0]),new File(args[1]),30);
    try(var files=Files.walk(root)) {
      for(Path p:files.filter(x->x.toString().endsWith(".smali")).sorted().toList())
        builder.buildFile(root.relativize(p).toString().replace('\\','/'),dex);
    }
    dex.writeTo(new FileDataStore(new File(args[1])));
  }
}
